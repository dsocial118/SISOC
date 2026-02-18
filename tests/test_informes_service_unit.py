"""Tests for informes service helper behavior and state transitions."""

from datetime import date, datetime
from io import BytesIO
from types import SimpleNamespace

import pytest
from django.utils import timezone

from admisiones.services import informes_service as module

pytestmark = pytest.mark.django_db


def test_base_url_and_form_queryset_helpers(mocker):
    """Simple helper selectors should return deterministic defaults."""
    mocker.patch(
        "admisiones.services.informes_service.settings.STATIC_ROOT", "/tmp/static"
    )
    assert module.InformeService._get_base_url() == "/tmp/static"

    assert (
        module.InformeService.get_form_class_por_tipo("juridico")
        is module.InformeTecnicoJuridicoForm
    )
    assert (
        module.InformeService.get_form_class_por_tipo("base")
        is module.InformeTecnicoBaseForm
    )
    assert module.InformeService.get_tipo_from_kwargs({"tipo": "x"}) == "x"

    q = SimpleNamespace()
    mocker.patch(
        "admisiones.services.informes_service.InformeTecnico.objects.filter",
        return_value=q,
    )
    assert module.InformeService.get_queryset_informe_por_tipo("base") is q


def test_get_admision_informe_by_kwargs_and_pk(mocker):
    """Lookup helpers should return fallback values on errors."""
    adm = SimpleNamespace(pk=1)
    mocker.patch(
        "admisiones.services.informes_service.get_object_or_404", return_value=adm
    )
    got_adm, got_tipo = module.InformeService.get_admision_y_tipo_from_kwargs(
        {"admision_id": 1, "tipo": "base"}
    )
    assert got_adm is adm and got_tipo == "base"

    mocker.patch(
        "admisiones.services.informes_service.get_object_or_404",
        side_effect=RuntimeError("x"),
    )
    got_adm2, got_tipo2 = module.InformeService.get_admision_y_tipo_from_kwargs(
        {"admision_id": 1}
    )
    assert got_adm2 is None and got_tipo2 == "base"

    assert module.InformeService.get_informe_por_tipo_y_pk("base", 1) is None


def test_estado_and_creation_preparation_helpers(mocker):
    """State helpers should update informe fields and dependent admission state."""
    delete1 = mocker.patch(
        "admisiones.services.informes_service.CampoASubsanar.objects.filter",
        return_value=SimpleNamespace(delete=mocker.Mock()),
    )
    delete2 = mocker.patch(
        "admisiones.services.informes_service.ObservacionGeneralInforme.objects.filter",
        return_value=SimpleNamespace(delete=mocker.Mock()),
    )

    inf = SimpleNamespace(pk=2, estado="Iniciado", estado_formulario="x")
    module.InformeService.verificar_estado_para_revision(inf, action=None)
    assert inf.estado == "Para revision"
    assert delete1.called and delete2.called

    inf2 = SimpleNamespace(admision_id=None, estado_formulario=None, estado=None)
    module.InformeService.preparar_informe_para_creacion(
        inf2, admision_id=8, action="draft"
    )
    assert inf2.estado == "Iniciado"

    admision = SimpleNamespace()
    informe = SimpleNamespace(pk=3, estado="x", admision=admision, save=mocker.Mock())
    upd = mocker.patch(
        "admisiones.services.admisiones_service.AdmisionService.actualizar_estado_admision"
    )
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
    field_choice = SimpleNamespace(
        name="campo_choice", choices=[("v", "Valor")], verbose_name="Choice"
    )

    assert module.InformeService._formatear_valor_campo(informe, field_bool) == "Sí"
    assert "2026" in module.InformeService._formatear_valor_campo(informe, field_dt)
    assert (
        module.InformeService._formatear_valor_campo(informe, field_choice) == "Valor"
    )

    informe._meta = SimpleNamespace(
        fields=[
            field_bool,
            field_dt,
            field_date,
            field_choice,
            SimpleNamespace(name="id", choices=None, verbose_name="ID"),
        ]
    )
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
    mocker.patch(
        "admisiones.services.informes_service.Document",
        side_effect=[FailDoc(), __import__("docx").Document()],
    )
    out = module.InformeService._generate_docx_content("<p>Hola</p>", informe_pk=2)
    assert out is not None


def test_generar_y_guardar_pdf_and_context_helpers(mocker):
    """Genera PDF/DOCX y cubre contextos de creación/actualización de informe."""
    informe = SimpleNamespace(
        id=10,
        pk=10,
        tipo="base",
        admision=SimpleNamespace(
            id=1, comedor=SimpleNamespace(nombre="C"), tipo="incorporacion"
        ),
    )

    mocker.patch(
        "admisiones.services.informes_service.generar_texto_comidas", return_value="txt"
    )
    mocker.patch(
        "admisiones.services.informes_service.render_to_string",
        side_effect=["<html>pdf</html>", "<html>docx</html>"],
    )
    mocker.patch(
        "admisiones.services.informes_service.HTML",
        return_value=SimpleNamespace(write_pdf=lambda: b"pdf"),
    )
    mocker.patch.object(
        module.InformeService,
        "generar_docx_con_template",
        return_value=BytesIO(b"docx"),
    )
    upd = mocker.patch(
        "admisiones.services.informes_service.InformeTecnicoPDF.objects.update_or_create",
        return_value=(SimpleNamespace(pk=1), True),
    )

    out = module.InformeService.generar_y_guardar_pdf(informe, "base")
    assert out is not None
    assert upd.called

    adm = SimpleNamespace(comedor=SimpleNamespace(nombre="X"))
    mocker.patch(
        "admisiones.services.informes_service.get_object_or_404", return_value=adm
    )
    ctx = module.InformeService.get_informe_create_context(1, "base")
    assert ctx["comedor"].nombre == "X"

    obs_exc = type("DoesNotExist", (Exception,), {})
    mocker.patch(
        "admisiones.services.informes_service.CampoASubsanar.objects.filter",
        return_value=SimpleNamespace(values_list=lambda *a, **k: ["campo_x"]),
    )
    mocker.patch(
        "admisiones.services.informes_service.ObservacionGeneralInforme.DoesNotExist",
        obs_exc,
    )
    mocker.patch(
        "admisiones.services.informes_service.ObservacionGeneralInforme.objects.get",
        side_effect=obs_exc(),
    )
    informe2 = SimpleNamespace(
        admision=SimpleNamespace(comedor=SimpleNamespace()),
        _meta=SimpleNamespace(
            fields=[SimpleNamespace(name="campo_x", verbose_name="Campo X")]
        ),
    )
    mocker.patch.object(
        module.InformeService,
        "get_campos_visibles_informe",
        return_value=[("Campo X", "v")],
    )
    ctx2 = module.InformeService.get_informe_update_context(informe2, "base")
    assert "campos_a_subsanar" in ctx2


def test_guardar_informe_and_detail_context(mocker):
    """Guarda informe en creación/edición y construye contexto de detalle."""
    admision = SimpleNamespace(id=2, estado_admision="x", save=mocker.Mock())
    instance = SimpleNamespace(
        tipo="base",
        pk=None,
        _state=SimpleNamespace(adding=True),
        estado_formulario="finalizado",
        observaciones_subsanacion="obs",
        admision=None,
        save=mocker.Mock(),
    )
    form = mocker.Mock(
        instance=instance,
        save=mocker.Mock(return_value=instance),
        save_m2m=mocker.Mock(),
    )

    mocker.patch(
        "admisiones.services.informes_service.InformeTecnico.objects.filter",
        return_value=SimpleNamespace(
            order_by=lambda *_: SimpleNamespace(first=lambda: None)
        ),
    )
    mocker.patch.object(
        module.InformeService, "generar_docx_borrador", return_value=SimpleNamespace()
    )
    mocker.patch(
        "admisiones.services.admisiones_service.AdmisionService.actualizar_estado_admision"
    )

    res = module.InformeService.guardar_informe(
        form, admision, es_creacion=True, action="submit", usuario=SimpleNamespace()
    )
    assert res["success"] is True

    informe_det = SimpleNamespace(
        admision=admision, estado="Validado", estado_formulario="finalizado", id=5
    )
    mocker.patch(
        "admisiones.services.informes_service.InformeTecnicoPDF.objects.filter",
        return_value=SimpleNamespace(first=lambda: "pdf"),
    )
    mocker.patch.object(
        module.InformeService, "get_campos_visibles_informe", return_value=[]
    )
    detail = module.InformeService.get_context_informe_detail(informe_det, "base")
    assert detail["pdf"] == "pdf"


def test_revision_and_complementarios_flows(mocker):
    """Procesa revisión y guarda cambios de complementario, incluyendo exportes."""
    field_obj = SimpleNamespace(
        name="campo",
        verbose_name="Campo",
        get_internal_type=lambda: "CharField",
    )
    informe = SimpleNamespace(
        id=3,
        pk=3,
        admision_id=3,
        tipo="base",
        admision=SimpleNamespace(id=3, comedor=SimpleNamespace()),
        _meta=SimpleNamespace(fields=[field_obj], get_field=lambda name: field_obj),
        observaciones_subsanacion=None,
        save=mocker.Mock(),
    )
    req = SimpleNamespace(
        POST=SimpleNamespace(
            get=lambda k, d=None: {"estado": "A subsanar", "observacion": "obs"}.get(
                k, d
            ),
            getlist=lambda k: ["Campo"],
        )
    )
    upd = mocker.patch.object(module.InformeService, "actualizar_estado_informe")
    mocker.patch(
        "admisiones.services.informes_service.CampoASubsanar.objects.filter",
        return_value=SimpleNamespace(delete=mocker.Mock()),
    )
    mocker.patch("admisiones.services.informes_service.CampoASubsanar.objects.create")
    mocker.patch(
        "admisiones.services.informes_service.ObservacionGeneralInforme.objects.get_or_create",
        return_value=(SimpleNamespace(texto="", save=mocker.Mock()), True),
    )
    module.InformeService.procesar_revision_informe(req, "base", informe)
    assert upd.called

    inf_comp = SimpleNamespace(
        pk=1,
        admision=informe.admision,
        informe_tecnico=informe,
        creado_por=SimpleNamespace(username="u"),
        creado=None,
    )
    mocker.patch(
        "admisiones.services.informes_service.InformeComplementario.objects.get_or_create",
        return_value=(inf_comp, True),
    )
    mocker.patch(
        "admisiones.services.informes_service.InformeComplementarioCampos.objects.filter",
        return_value=SimpleNamespace(delete=mocker.Mock()),
    )
    create = mocker.patch(
        "admisiones.services.informes_service.InformeComplementarioCampos.objects.create"
    )
    saved = module.InformeService.guardar_campos_complementarios(
        informe, {"campo": "valor"}, usuario=SimpleNamespace()
    )
    assert saved is inf_comp
    assert create.called

    campo_obj = SimpleNamespace(campo="campo", value="nuevo")
    mocker.patch(
        "admisiones.services.informes_service.InformeComplementarioCampos.objects.filter",
        return_value=[campo_obj],
    )
    mocker.patch(
        "admisiones.services.informes_service.generar_texto_comidas", return_value="txt"
    )
    mocker.patch(
        "admisiones.services.informes_service.render_to_string",
        return_value="<html></html>",
    )
    mocker.patch(
        "admisiones.services.informes_service.HTML",
        return_value=SimpleNamespace(write_pdf=lambda: b"pdf"),
    )
    mocker.patch(
        "admisiones.services.informes_service.DocumentTemplateService.generar_docx",
        return_value=BytesIO(b"docx"),
    )
    mocker.patch(
        "admisiones.services.informes_service.InformeTecnicoComplementarioPDF.objects.update_or_create"
    )
    assert module.InformeService.generar_y_guardar_pdf_complementario(inf_comp) is True

    mocker.patch.object(
        module.InformeService,
        "generar_docx_con_template",
        return_value=BytesIO(b"docx"),
    )
    mocker.patch(
        "admisiones.services.informes_service.InformeTecnicoPDF.objects.update_or_create",
        return_value=(SimpleNamespace(pk=1), True),
    )
    borrador = module.InformeService.generar_docx_borrador(
        SimpleNamespace(
            id=4,
            pk=4,
            tipo="base",
            estado="Iniciado",
            admision=SimpleNamespace(id=4, comedor=SimpleNamespace()),
            admision_id=4,
            save=mocker.Mock(),
        )
    )
    assert borrador is not None

    pdf_obj = SimpleNamespace(save=mocker.Mock())
    mocker.patch(
        "admisiones.services.informes_service.InformeTecnicoPDF.objects.get_or_create",
        return_value=(pdf_obj, False),
    )
    mocker.patch(
        "admisiones.services.admisiones_service.AdmisionService.actualizar_estado_admision"
    )
    informe_upload = SimpleNamespace(
        id=8,
        pk=8,
        tipo="base",
        estado="x",
        admision=SimpleNamespace(id=8, comedor=SimpleNamespace()),
        admision_id=8,
        save=mocker.Mock(),
    )
    archivo = SimpleNamespace(name="x")
    assert module.InformeService.subir_docx_editado(informe_upload, archivo) is pdf_obj

    mocker.patch(
        "admisiones.services.informes_service.InformeComplementarioCampos.objects.filter",
        return_value=[SimpleNamespace()],
    )
    assert module.InformeService.obtener_cambios_complementarios_texto(inf_comp)
