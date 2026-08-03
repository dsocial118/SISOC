import pytest

from admisiones.forms.admisiones_forms import ValidacionesTemplateAdmisionForm
from admisiones.models.admisiones import Admision
from admisiones.services.admisiones_service import AdmisionService


pytestmark = pytest.mark.django_db


def test_incorporacion_ex_pnud_no_limpia_estado_convenio_pnud():
    admision = Admision.objects.create(
        tipo="incorporacion",
        estado_convenio_pnud="vigente",
    )

    form = ValidacionesTemplateAdmisionForm(
        {"es_ex_pnud": "no", "estado_convenio_pnud": "vigente"},
        instance=admision,
    )

    assert form.is_valid()
    actualizada = form.save()

    assert actualizada.es_ex_pnud == "no"
    assert actualizada.estado_convenio_pnud is None
    assert actualizada.tipo_renovacion is None
    assert actualizada.estado_financiamiento is None


def test_incorporacion_ex_pnud_si_requiere_estado_convenio():
    admision = Admision.objects.create(tipo="incorporacion")

    form = ValidacionesTemplateAdmisionForm(
        {"es_ex_pnud": "si"},
        instance=admision,
    )

    assert not form.is_valid()
    assert "estado_convenio_pnud" in form.errors


def test_renovacion_guarda_solo_sus_validaciones():
    admision = Admision.objects.create(
        tipo="renovacion",
        es_ex_pnud="si",
        estado_convenio_pnud="vigente",
    )

    form = ValidacionesTemplateAdmisionForm(
        {
            "tipo_renovacion": "segunda_o_posterior",
            "estado_financiamiento": "finalizado",
        },
        instance=admision,
    )

    assert form.is_valid()
    actualizada = form.save()

    assert actualizada.tipo_renovacion == "segunda_o_posterior"
    assert actualizada.estado_financiamiento == "finalizado"
    assert actualizada.es_ex_pnud is None
    assert actualizada.estado_convenio_pnud is None


def test_no_permite_guardar_validaciones_despues_de_generar_informe(monkeypatch):
    admision = Admision.objects.create(tipo="incorporacion")
    monkeypatch.setattr(
        AdmisionService,
        "puede_editar_validaciones_template",
        lambda _admision: False,
    )

    success, message = AdmisionService.guardar_validaciones_template(
        admision,
        {"es_ex_pnud": "no"},
    )

    assert not success
    assert "después de generar" in message
