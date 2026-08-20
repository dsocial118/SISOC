"""Finalizacion de acompanamientos: reglas de negocio sobre el modelo y el service."""

import pytest

from acompanamientos.acompanamiento_service import AcompanamientoService
from acompanamientos.models.acompanamiento import Acompanamiento
from admisiones.models.admisiones import Admision
from comedores.models import Comedor


pytestmark = pytest.mark.django_db


def _crear_acompanamiento(activa=True, nro_convenio="CONV-1"):
    comedor = Comedor.objects.create(nombre="Comedor Alimentar")
    admision = Admision.objects.create(
        comedor=comedor,
        activa=activa,
        enviado_acompaniamiento=True,
        estado_admision="informe_tecnico_aprobado",
    )
    acompanamiento = Acompanamiento.objects.create(
        admision=admision,
        nro_convenio=nro_convenio,
    )
    return comedor, admision, acompanamiento


def test_finalizar_marca_fecha_y_usuario(superuser):
    comedor, admision, acompanamiento = _crear_acompanamiento()

    resultado, error = AcompanamientoService.finalizar_acompanamiento(
        comedor, admision.id, superuser
    )

    assert error is None
    assert resultado.pk == acompanamiento.pk

    acompanamiento.refresh_from_db()
    assert acompanamiento.fecha_finalizado is not None
    assert acompanamiento.finalizado_por == superuser
    assert acompanamiento.finalizado is True
    assert acompanamiento.es_gestionable is False
    assert acompanamiento.puede_finalizarse is False


def test_finalizar_no_inactiva_la_admision(superuser):
    """Finalizar y cerrar son estados distintos: la admision sigue activa."""

    comedor, admision, _ = _crear_acompanamiento()

    AcompanamientoService.finalizar_acompanamiento(comedor, admision.id, superuser)

    admision.refresh_from_db()
    assert admision.activa is True
    assert admision.estado_mostrar != "Inactivada"


def test_finalizar_es_idempotente_y_rechaza_el_segundo_intento(superuser):
    comedor, admision, acompanamiento = _crear_acompanamiento()

    AcompanamientoService.finalizar_acompanamiento(comedor, admision.id, superuser)
    acompanamiento.refresh_from_db()
    fecha_original = acompanamiento.fecha_finalizado

    resultado, error = AcompanamientoService.finalizar_acompanamiento(
        comedor, admision.id, superuser
    )

    assert resultado is None
    assert error == "El acompañamiento ya se encuentra finalizado."

    acompanamiento.refresh_from_db()
    assert acompanamiento.fecha_finalizado == fecha_original


def test_no_puede_finalizarse_si_la_admision_fue_cerrada(superuser):
    comedor, admision, acompanamiento = _crear_acompanamiento(activa=False)

    assert acompanamiento.puede_finalizarse is False

    resultado, error = AcompanamientoService.finalizar_acompanamiento(
        comedor, admision.id, superuser
    )

    assert resultado is None
    assert "cerrada" in error

    acompanamiento.refresh_from_db()
    assert acompanamiento.fecha_finalizado is None


def test_no_finaliza_un_acompanamiento_de_otro_comedor(superuser):
    _, admision, acompanamiento = _crear_acompanamiento()
    otro_comedor = Comedor.objects.create(nombre="Otro comedor")

    resultado, error = AcompanamientoService.finalizar_acompanamiento(
        otro_comedor, admision.id, superuser
    )

    assert resultado is None
    assert error == "No se encontró el acompañamiento del convenio indicado."

    acompanamiento.refresh_from_db()
    assert acompanamiento.fecha_finalizado is None


def test_el_selector_de_convenios_sigue_trayendo_los_finalizados(superuser):
    comedor, admision, _ = _crear_acompanamiento()

    AcompanamientoService.finalizar_acompanamiento(comedor, admision.id, superuser)

    admisiones = list(AcompanamientoService.obtener_admisiones_para_selector(comedor))

    assert [a.id for a in admisiones] == [admision.id]
    assert admisiones[0].acompanamiento.finalizado is True
