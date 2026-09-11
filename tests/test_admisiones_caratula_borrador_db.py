"""Caratulación del expediente con borrador, igual que el informe técnico.

Reglas:
 - la carga documental no condiciona la caratulación: la documentación se
   puede sumar en cualquier momento del proceso;
 - en borrador se guarda el avance aunque esté incompleto, sin validar
   duplicados y sin mover el estado de la admisión;
 - al finalizar se valida todo, se compila ``num_expediente`` y el borrador se
   limpia.
"""

import pytest

from admisiones.models.admisiones import (
    Admision,
    ArchivoAdmision,
    Documentacion,
    TipoConvenio,
)
from admisiones.services.admisiones_service import AdmisionService
from comedores.models import Comedor

pytestmark = pytest.mark.django_db

PREFIJO = "caratula"
CARATULA_COMPLETA = {
    f"{PREFIJO}-expediente_anio": "2026",
    f"{PREFIJO}-expediente_numero": "112100154",
    f"{PREFIJO}-expediente_reparticion": "DDNAYF",
    f"{PREFIJO}-expediente_organismo": "MCH",
}
NUMERO_COMPILADO = "EX-2026-112100154- -APN-DDNAYF#MCH"


def _crear_admision(estado_admision="documentacion_en_proceso", aceptados=True):
    comedor = Comedor.objects.create(nombre=f"Comedor {Comedor.objects.count() + 1}")
    tipo_convenio = TipoConvenio.objects.create(
        nombre=f"Convenio {TipoConvenio.objects.count() + 1}"
    )
    admision = Admision.objects.create(
        comedor=comedor,
        tipo_convenio=tipo_convenio,
        tipo="incorporacion",
        estado_admision=estado_admision,
    )
    documentacion = Documentacion.objects.create(
        nombre="Documento obligatorio", obligatorio=True, orden=1
    )
    documentacion.convenios.add(tipo_convenio)
    ArchivoAdmision.objects.create(
        admision=admision,
        documentacion=documentacion,
        estado="Aceptado" if aceptados else "pendiente",
        archivo="admisiones/test.pdf",
    )
    return admision


# --- La carga documental ya no condiciona la caratulación ----------------


@pytest.mark.parametrize(
    "estado",
    [
        "documentacion_en_proceso",
        "documentacion_aprobada",
        "documentacion_carga_finalizada",
    ],
)
def test_carátula_no_depende_del_estado_de_la_carga_documental(estado):
    admision = _crear_admision(estado)

    ok, mensaje, _form = AdmisionService.guardar_caratulacion(
        admision, CARATULA_COMPLETA, prefix=PREFIJO
    )

    assert ok is True, mensaje
    admision.refresh_from_db()
    assert admision.num_expediente == NUMERO_COMPILADO
    assert admision.estado_admision == "expediente_cargado"


def test_carátula_funciona_con_obligatorios_sin_aceptar():
    """La documentación se puede seguir sumando después de caratular."""
    admision = _crear_admision("documentacion_en_proceso", aceptados=False)

    ok, _mensaje, _form = AdmisionService.guardar_caratulacion(
        admision, CARATULA_COMPLETA, prefix=PREFIJO
    )

    assert ok is True


def test_ya_no_existe_el_paso_de_finalizar_carga_encadenado():
    assert not hasattr(
        AdmisionService, "finalizar_carga_documentacion_si_corresponde"
    ), "la lógica encadenada de finalizar carga debía quedar fuera"
    # El paso suelto, con su propio botón, sigue disponible.
    assert hasattr(AdmisionService, "_procesar_post_finalizar_carga_documentacion")


# --- Borrador -------------------------------------------------------------


def test_borrador_guarda_una_caratula_incompleta():
    admision = _crear_admision()

    ok, mensaje, _form = AdmisionService.guardar_caratulacion(
        admision,
        {f"{PREFIJO}-expediente_anio": "2026"},
        prefix=PREFIJO,
        borrador=True,
    )

    assert ok is True, mensaje
    admision.refresh_from_db()
    assert admision.num_expediente_borrador == "EX-2026-- -APN-#"
    # El borrador no caratula ni mueve el estado.
    assert admision.num_expediente is None
    assert admision.estado_admision == "documentacion_en_proceso"


def test_borrador_vacio_no_guarda_nada():
    """Solo el organismo precargado no es un borrador con contenido."""
    admision = _crear_admision()

    ok, _mensaje, _form = AdmisionService.guardar_caratulacion(
        admision,
        {f"{PREFIJO}-expediente_organismo": "MCH"},
        prefix=PREFIJO,
        borrador=True,
    )

    assert ok is True
    admision.refresh_from_db()
    assert admision.num_expediente_borrador is None


def test_borrador_no_valida_duplicados():
    """Un número repetido recién se rechaza al finalizar."""
    otra = _crear_admision()
    otra.num_expediente = NUMERO_COMPILADO
    otra.save()
    admision = _crear_admision()

    ok, _mensaje, _form = AdmisionService.guardar_caratulacion(
        admision, CARATULA_COMPLETA, prefix=PREFIJO, borrador=True
    )

    assert ok is True
    admision.refresh_from_db()
    assert admision.num_expediente_borrador == NUMERO_COMPILADO
    assert admision.num_expediente is None


def test_el_borrador_vuelve_precargado_al_formulario():
    admision = _crear_admision()
    AdmisionService.guardar_caratulacion(
        admision,
        {
            f"{PREFIJO}-expediente_anio": "2026",
            f"{PREFIJO}-expediente_reparticion": "ddnayf",
        },
        prefix=PREFIJO,
        borrador=True,
    )
    admision.refresh_from_db()

    from admisiones.forms.admisiones_forms import CaratularForm

    form = CaratularForm(instance=admision, prefix=PREFIJO, borrador=True)

    assert form.initial["expediente_anio"] == "2026"
    assert form.initial["expediente_reparticion"] == "DDNAYF"
    assert "expediente_numero" not in form.initial


def test_al_finalizar_se_guarda_el_borrador_y_se_limpia():
    admision = _crear_admision()
    AdmisionService.guardar_caratulacion(
        admision, CARATULA_COMPLETA, prefix=PREFIJO, borrador=True
    )
    admision.refresh_from_db()
    assert admision.num_expediente_borrador == NUMERO_COMPILADO

    ok, _mensaje, _form = AdmisionService.guardar_caratulacion(
        admision, CARATULA_COMPLETA, prefix=PREFIJO
    )

    assert ok is True
    admision.refresh_from_db()
    assert admision.num_expediente == NUMERO_COMPILADO
    assert admision.num_expediente_borrador is None
    assert admision.estado_admision == "expediente_cargado"


def test_finalizar_sigue_exigiendo_los_campos_completos():
    admision = _crear_admision()

    ok, mensaje, form = AdmisionService.guardar_caratulacion(
        admision, {f"{PREFIJO}-expediente_anio": "2026"}, prefix=PREFIJO
    )

    assert ok is False
    assert mensaje == "Error al guardar la caratulación."
    assert "expediente_numero" in form.errors
    admision.refresh_from_db()
    assert admision.num_expediente is None


def test_finalizar_sigue_rechazando_duplicados():
    otra = _crear_admision()
    otra.num_expediente = NUMERO_COMPILADO
    otra.save()
    admision = _crear_admision()

    ok, _mensaje, form = AdmisionService.guardar_caratulacion(
        admision, CARATULA_COMPLETA, prefix=PREFIJO
    )

    assert ok is False
    assert "ya pertenece a la admisión" in str(form.errors)


# --- Integración con el guardado del informe ------------------------------


def test_la_vista_guarda_caratula_en_borrador_y_el_informe(mocker):
    from admisiones.views.web_views import AdmisionesTecnicosUpdateView

    admision = _crear_admision()
    vista = AdmisionesTecnicosUpdateView()
    request = mocker.Mock(POST=dict(CARATULA_COMPLETA), FILES={}, user=None)
    mocker.patch(
        "admisiones.views.web_views.InformeService.guardar_informe",
        return_value={"success": True, "informe": mocker.Mock(pk=1)},
    )

    caratular_form, error = vista._guardar_informe_y_caratula(
        request, admision, mocker.Mock(instance=mocker.Mock(pk=None)), "draft"
    )

    assert (caratular_form, error) == (None, None)
    admision.refresh_from_db()
    assert admision.num_expediente_borrador == NUMERO_COMPILADO
    assert admision.num_expediente is None


def test_la_vista_caratula_de_verdad_al_finalizar(mocker):
    from admisiones.views.web_views import AdmisionesTecnicosUpdateView

    admision = _crear_admision()
    vista = AdmisionesTecnicosUpdateView()
    request = mocker.Mock(POST=dict(CARATULA_COMPLETA), FILES={}, user=None)
    mocker.patch(
        "admisiones.views.web_views.InformeService.guardar_informe",
        return_value={"success": True, "informe": mocker.Mock(pk=1)},
    )

    _caratular_form, error = vista._guardar_informe_y_caratula(
        request, admision, mocker.Mock(instance=mocker.Mock(pk=None)), "submit"
    )

    assert error is None
    admision.refresh_from_db()
    assert admision.num_expediente == NUMERO_COMPILADO
    assert admision.estado_admision == "expediente_cargado"


def test_un_borrador_vacio_no_bloquea_el_guardado_del_informe(mocker):
    """Regresión: la carátula obligatoria rompía el borrador del informe."""
    from admisiones.views.web_views import AdmisionesTecnicosUpdateView

    admision = _crear_admision()
    vista = AdmisionesTecnicosUpdateView()
    request = mocker.Mock(POST={}, FILES={}, user=None)
    guardar_informe = mocker.patch(
        "admisiones.views.web_views.InformeService.guardar_informe",
        return_value={"success": True, "informe": mocker.Mock(pk=1)},
    )

    caratular_form, error = vista._guardar_informe_y_caratula(
        request, admision, mocker.Mock(instance=mocker.Mock(pk=None)), "draft"
    )

    assert (caratular_form, error) == (None, None)
    guardar_informe.assert_called_once()


def test_si_falla_el_informe_no_queda_caratulado(mocker):
    from admisiones.views.web_views import AdmisionesTecnicosUpdateView

    admision = _crear_admision()
    vista = AdmisionesTecnicosUpdateView()
    request = mocker.Mock(POST=dict(CARATULA_COMPLETA), FILES={}, user=None)
    mocker.patch(
        "admisiones.views.web_views.InformeService.guardar_informe",
        return_value={"success": False, "error": "no se pudo"},
    )

    _caratular_form, error = vista._guardar_informe_y_caratula(
        request, admision, mocker.Mock(instance=mocker.Mock(pk=None)), "submit"
    )

    assert error == "no se pudo"
    admision.refresh_from_db()
    assert admision.num_expediente is None


def test_no_recaratula_una_admision_que_ya_tiene_expediente(mocker):
    from admisiones.views.web_views import AdmisionesTecnicosUpdateView

    admision = _crear_admision()
    admision.num_expediente = "EX-2020-000000001- -APN-OTRA#MCH"
    admision.save()
    vista = AdmisionesTecnicosUpdateView()
    request = mocker.Mock(POST=dict(CARATULA_COMPLETA), FILES={}, user=None)
    mocker.patch(
        "admisiones.views.web_views.InformeService.guardar_informe",
        return_value={"success": True, "informe": mocker.Mock(pk=1)},
    )

    _caratular_form, error = vista._guardar_informe_y_caratula(
        request, admision, mocker.Mock(instance=mocker.Mock(pk=None)), "submit"
    )

    assert error is None
    admision.refresh_from_db()
    assert admision.num_expediente == "EX-2020-000000001- -APN-OTRA#MCH"
