"""Un único botón encadena finalizar carga, caratular e informe técnico.

Los tres pasos van en una transacción y en el orden que impone la máquina de
estados, así que ninguna validación se saltea y nada queda a medio aplicar.
"""

import pytest

from admisiones.models.admisiones import (
    Admision,
    ArchivoAdmision,
    Documentacion,
    InformeTecnico,
    TipoConvenio,
)
from admisiones.services.admisiones_service import AdmisionService
from comedores.models import Comedor

pytestmark = pytest.mark.django_db

CARATULA_OK = {
    "caratula-expediente_anio": "2026",
    "caratula-expediente_numero": "112100154",
    "caratula-expediente_reparticion": "DDNAYF",
    "caratula-expediente_organismo": "MCH",
}


def _crear_admision(estado_admision, documentos_aceptados=True):
    comedor = Comedor.objects.create(nombre=f"Comedor {estado_admision}")
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
        estado="Aceptado" if documentos_aceptados else "pendiente",
        archivo="admisiones/test.pdf",
    )
    return admision


# --- El paso de finalizar carga documental --------------------------------


def test_finaliza_la_carga_cuando_la_admision_esta_lista():
    admision = _crear_admision("documentacion_aprobada")

    ok, mensaje = AdmisionService.finalizar_carga_documentacion_si_corresponde(admision)

    assert ok is True
    assert mensaje == "Carga de documentación finalizada correctamente."
    admision.refresh_from_db()
    assert admision.estado_admision == "documentacion_carga_finalizada"


def test_no_hace_nada_si_la_carga_ya_estaba_finalizada():
    admision = _crear_admision("documentacion_carga_finalizada")

    ok, mensaje = AdmisionService.finalizar_carga_documentacion_si_corresponde(admision)

    assert (ok, mensaje) == (True, None)
    admision.refresh_from_db()
    assert admision.estado_admision == "documentacion_carga_finalizada"


def test_rechaza_finalizar_con_obligatorios_sin_validar():
    admision = _crear_admision("documentacion_aprobada", documentos_aceptados=False)

    ok, mensaje = AdmisionService.finalizar_carga_documentacion_si_corresponde(admision)

    assert ok is False
    assert "sin validar" in mensaje
    admision.refresh_from_db()
    assert admision.estado_admision == "documentacion_aprobada"


def test_rechaza_finalizar_sin_archivo_en_un_obligatorio():
    admision = _crear_admision("documentacion_aprobada")
    ArchivoAdmision.objects.filter(admision=admision).delete()

    ok, mensaje = AdmisionService.finalizar_carga_documentacion_si_corresponde(admision)

    assert ok is False
    assert "faltan documentos obligatorios" in mensaje.lower()


# --- El encadenado completo desde la vista --------------------------------


def _vista_con_post(admision, post, mocker):
    from admisiones.views.web_views import AdmisionesTecnicosUpdateView

    vista = AdmisionesTecnicosUpdateView()
    request = mocker.Mock(POST=post, FILES={}, user=None)
    return vista, request


def test_un_solo_paso_encadena_finalizar_caratular_e_informe(mocker):
    """Desde `documentacion_aprobada` llega hasta el informe iniciado."""
    admision = _crear_admision("documentacion_aprobada")
    vista, request = _vista_con_post(admision, dict(CARATULA_OK), mocker)

    informe_form = mocker.Mock(instance=mocker.Mock(pk=None))
    mocker.patch(
        "admisiones.views.web_views.InformeService.guardar_informe",
        return_value={"success": True, "informe": mocker.Mock(pk=1)},
    )

    caratular_form, error = vista._guardar_informe_y_caratula(
        request, admision, informe_form, "submit"
    )

    assert (caratular_form, error) == (None, None)
    admision.refresh_from_db()
    assert admision.estado_admision == "expediente_cargado"
    assert admision.num_expediente == "EX-2026-112100154- -APN-DDNAYF#MCH"


def test_si_falla_el_informe_no_queda_caratulado(mocker):
    """La transacción es todo o nada."""
    admision = _crear_admision("documentacion_aprobada")
    vista, request = _vista_con_post(admision, dict(CARATULA_OK), mocker)

    informe_form = mocker.Mock(instance=mocker.Mock(pk=None))
    mocker.patch(
        "admisiones.views.web_views.InformeService.guardar_informe",
        return_value={"success": False, "error": "no se pudo"},
    )

    _caratular_form, error = vista._guardar_informe_y_caratula(
        request, admision, informe_form, "submit"
    )

    assert error == "no se pudo"
    admision.refresh_from_db()
    assert admision.num_expediente is None
    assert admision.estado_admision == "documentacion_aprobada"


def test_si_no_se_puede_finalizar_la_carga_no_caratula(mocker):
    admision = _crear_admision("documentacion_aprobada", documentos_aceptados=False)
    vista, request = _vista_con_post(admision, dict(CARATULA_OK), mocker)

    guardar_informe = mocker.patch(
        "admisiones.views.web_views.InformeService.guardar_informe"
    )

    _caratular_form, error = vista._guardar_informe_y_caratula(
        request, admision, mocker.Mock(instance=mocker.Mock(pk=None)), "submit"
    )

    assert "sin validar" in error
    guardar_informe.assert_not_called()
    admision.refresh_from_db()
    assert admision.num_expediente is None


# --- El borrador no queda bloqueado por la carátula ----------------------


def test_borrador_con_caratula_vacia_guarda_el_informe(mocker):
    """Regresión: exigir la carátula en borrador bloqueaba el guardado."""
    admision = _crear_admision("documentacion_aprobada")
    vista, request = _vista_con_post(admision, {}, mocker)

    guardar_informe = mocker.patch(
        "admisiones.views.web_views.InformeService.guardar_informe",
        return_value={"success": True, "informe": mocker.Mock(pk=1)},
    )

    caratular_form, error = vista._guardar_informe_y_caratula(
        request, admision, mocker.Mock(instance=mocker.Mock(pk=None)), "draft"
    )

    assert (caratular_form, error) == (None, None)
    guardar_informe.assert_called_once()
    admision.refresh_from_db()
    # El borrador no avanza el estado si el usuario no cargó el expediente.
    assert admision.estado_admision == "documentacion_aprobada"
    assert admision.num_expediente is None


def test_borrador_con_caratula_cargada_si_la_guarda(mocker):
    admision = _crear_admision("documentacion_aprobada")
    vista, request = _vista_con_post(admision, dict(CARATULA_OK), mocker)

    mocker.patch(
        "admisiones.views.web_views.InformeService.guardar_informe",
        return_value={"success": True, "informe": mocker.Mock(pk=1)},
    )

    _caratular_form, error = vista._guardar_informe_y_caratula(
        request, admision, mocker.Mock(instance=mocker.Mock(pk=None)), "draft"
    )

    assert error is None
    admision.refresh_from_db()
    assert admision.num_expediente == "EX-2026-112100154- -APN-DDNAYF#MCH"


def test_no_recaratula_una_admision_que_ya_tiene_expediente(mocker):
    admision = _crear_admision("informe_tecnico_en_proceso")
    admision.num_expediente = "EX-2020-000000001- -APN-OTRA#MCH"
    admision.save()
    vista, request = _vista_con_post(admision, dict(CARATULA_OK), mocker)

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
