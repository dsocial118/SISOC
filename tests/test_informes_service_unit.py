"""Tests for informes service helper behavior and state transitions."""

from datetime import date, datetime
from types import SimpleNamespace

import pytest
from django.utils import timezone

from admisiones.services import informes_service as module

pytestmark = pytest.mark.django_db


def test_base_url_and_form_queryset_helpers(mocker):
    """Simple helper selectors should return deterministic defaults."""
    mocker.patch("admisiones.services.informes_service.settings.STATIC_ROOT", "/tmp/static")
    assert module.InformeService._get_base_url() == "/tmp/static"

    assert module.InformeService.get_form_class_por_tipo("juridico") is module.InformeTecnicoJuridicoForm
    assert module.InformeService.get_form_class_por_tipo("base") is module.InformeTecnicoBaseForm
    assert module.InformeService.get_tipo_from_kwargs({"tipo": "x"}) == "x"

    q = SimpleNamespace()
    mocker.patch("admisiones.services.informes_service.InformeTecnico.objects.filter", return_value=q)
    assert module.InformeService.get_queryset_informe_por_tipo("base") is q


def test_get_admision_informe_by_kwargs_and_pk(mocker):
    """Lookup helpers should return fallback values on errors."""
    adm = SimpleNamespace(pk=1)
    mocker.patch("admisiones.services.informes_service.get_object_or_404", return_value=adm)
    got_adm, got_tipo = module.InformeService.get_admision_y_tipo_from_kwargs({"admision_id": 1, "tipo": "base"})
    assert got_adm is adm and got_tipo == "base"

    mocker.patch("admisiones.services.informes_service.get_object_or_404", side_effect=RuntimeError("x"))
    got_adm2, got_tipo2 = module.InformeService.get_admision_y_tipo_from_kwargs({"admision_id": 1})
    assert got_adm2 is None and got_tipo2 == "base"

    assert module.InformeService.get_informe_por_tipo_y_pk("base", 1) is None


def test_estado_and_creation_preparation_helpers(mocker):
    """State helpers should update informe fields and dependent admission state."""
    delete1 = mocker.patch("admisiones.services.informes_service.CampoASubsanar.objects.filter", return_value=SimpleNamespace(delete=mocker.Mock()))
    delete2 = mocker.patch("admisiones.services.informes_service.ObservacionGeneralInforme.objects.filter", return_value=SimpleNamespace(delete=mocker.Mock()))

    inf = SimpleNamespace(pk=2, estado="Iniciado", estado_formulario="x")
    module.InformeService.verificar_estado_para_revision(inf, action=None)
    assert inf.estado == "Para revision"
    assert delete1.called and delete2.called

    inf2 = SimpleNamespace(admision_id=None, estado_formulario=None, estado=None)
    module.InformeService.preparar_informe_para_creacion(inf2, admision_id=8, action="draft")
    assert inf2.estado == "Iniciado"

    admision = SimpleNamespace()
    informe = SimpleNamespace(pk=3, estado="x", admision=admision, save=mocker.Mock())
    upd = mocker.patch("admisiones.services.admisiones_service.AdmisionService.actualizar_estado_admision")
    module.InformeService.actualizar_estado_informe(informe, "Validado")
    assert upd.called


def test_formateo_campos_and_visibles(mocker):
    """Field formatters should render booleans, dates and display labels."""
    aware = timezone.make_aware(datetime(2026, 1, 2, 3, 4))
    informe = SimpleNamespace(
        tipo="base",
        campo_bool=True,
        campo_dt=aware,
        campo_date=date(2026, 1, 2),
        campo_choice="v",
        get_campo_choice_display=lambda: "Valor",
    )

    field_bool = SimpleNamespace(name="campo_bool", choices=None, verbose_name="Bool")
    field_dt = SimpleNamespace(name="campo_dt", choices=None, verbose_name="DT")
    field_date = SimpleNamespace(name="campo_date", choices=None, verbose_name="Date")
    field_choice = SimpleNamespace(name="campo_choice", choices=[("v", "Valor")], verbose_name="Choice")

    assert module.InformeService._formatear_valor_campo(informe, field_bool) == "Sí"
    assert "2026" in module.InformeService._formatear_valor_campo(informe, field_dt)
    assert module.InformeService._formatear_valor_campo(informe, field_choice) == "Valor"

    informe._meta = SimpleNamespace(fields=[field_bool, field_dt, field_date, field_choice, SimpleNamespace(name="id", choices=None, verbose_name="ID")])
    visibles = module.InformeService.get_campos_visibles_informe(informe)
    assert len(visibles) >= 4


def test_generate_docx_content_primary_and_fallback(mocker):
    """DOCX generation should return content in normal and fallback branches."""
    file_obj = module.InformeService._generate_docx_content("<p>Hola</p>", informe_pk=1)
    assert file_obj is not None

    class FailDoc:
        def save(self, *_a, **_k):
            raise RuntimeError("x")

        def add_paragraph(self, *_a, **_k):
            return None

    # fail first path, succeed fallback with real Document instance
    mocker.patch("admisiones.services.informes_service.Document", side_effect=[FailDoc(), __import__("docx").Document()])
    out = module.InformeService._generate_docx_content("<p>Hola</p>", informe_pk=2)
    assert out is not None
