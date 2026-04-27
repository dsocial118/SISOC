"""Tests for primer seguimiento de relevamiento de comedor."""

import json

import pytest
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.urls import reverse

from comedores.models import Comedor
from relevamientos.models import (
    PrimerSeguimiento,
    Relevamiento,
    ServiciosBasicosSeguimiento,
)
from relevamientos.primer_seguimiento_service import PrimerSeguimientoService
from relevamientos.tasks import build_primer_seguimiento_payload


pytestmark = pytest.mark.django_db


def _territorial_payload(uid="uid-1", nombre="Territorial Norte"):
    return json.dumps({"gestionar_uid": uid, "nombre": nombre})


@pytest.fixture
def comedor():
    return Comedor.objects.create(
        nombre="Comedor Primer Seguimiento",
        codigo_de_proyecto="PNUD-001",
    )


@pytest.fixture(autouse=True)
def _disable_relevamiento_sync(monkeypatch):
    monkeypatch.setattr(
        "relevamientos.signals.AsyncSendRelevamientoToGestionar.start",
        lambda self: None,
    )
    monkeypatch.setattr(
        "relevamientos.signals.AsyncRemoveRelevamientoToGestionar.start",
        lambda self: None,
    )


def test_modelo_deriva_cod_pnud_y_valida_escala(comedor):
    relevamiento = Relevamiento.objects.create(comedor=comedor, estado="En Proceso")
    seguimiento = PrimerSeguimiento.objects.create(
        id_relevamiento=relevamiento,
        estado=PrimerSeguimiento.ESTADO_ASIGNADO,
    )

    assert seguimiento.cod_pnud == "PNUD-001"

    bloque = ServiciosBasicosSeguimiento(agua_potable=True, gas_red=5)
    with pytest.raises(DjangoValidationError):
        bloque.full_clean()


def test_primer_seguimiento_bloquea_duplicado_por_ancla(comedor):
    relevamiento = Relevamiento.objects.create(comedor=comedor, estado="En Proceso")
    PrimerSeguimiento.objects.create(
        id_relevamiento=relevamiento,
        estado=PrimerSeguimiento.ESTADO_ASIGNADO,
    )

    with pytest.raises(IntegrityError):
        PrimerSeguimiento.objects.create(
            id_relevamiento=relevamiento,
            estado=PrimerSeguimiento.ESTADO_ASIGNADO,
        )


def test_servicio_usa_ultimo_relevamiento_activo_no_finalizado(comedor, mocker):
    Relevamiento.objects.create(comedor=comedor, estado="En Proceso")
    esperado = Relevamiento.objects.create(comedor=comedor, estado="Pendiente")
    Relevamiento.objects.create(comedor=comedor, estado="Finalizado")
    send_task = mocker.patch(
        "relevamientos.primer_seguimiento_service.AsyncSendPrimerSeguimientoToGestionar"
    )

    seguimiento = PrimerSeguimientoService.create_asignado(
        comedor.id,
        _territorial_payload(),
    )

    assert seguimiento.id_relevamiento_id == esperado.id
    assert seguimiento.estado == PrimerSeguimiento.ESTADO_ASIGNADO
    assert seguimiento.tecnico == "uid-1"
    assert Relevamiento.objects.filter(comedor=comedor).count() == 3
    send_task.assert_called_once()
    send_task.return_value.start.assert_called_once_with()


def test_servicio_crea_ancla_local_sin_sync_inicial_si_no_existe(comedor, mocker):
    initial_sync = mocker.patch(
        "relevamientos.signals.AsyncSendRelevamientoToGestionar.start"
    )
    send_task = mocker.patch(
        "relevamientos.primer_seguimiento_service.AsyncSendPrimerSeguimientoToGestionar"
    )

    seguimiento = PrimerSeguimientoService.create_asignado(
        comedor.id,
        _territorial_payload(),
    )

    relevamiento = seguimiento.id_relevamiento
    assert relevamiento.comedor_id == comedor.id
    assert relevamiento.territorial_uid is None
    assert initial_sync.call_count == 0
    assert send_task.called


def test_servicio_exige_territorial_valido(comedor):
    with pytest.raises(DjangoValidationError):
        PrimerSeguimientoService.create_asignado(comedor.id, "")


def test_servicio_bloquea_duplicado_por_ancla_activa(comedor):
    relevamiento = Relevamiento.objects.create(comedor=comedor, estado="En Proceso")
    PrimerSeguimiento.objects.create(
        id_relevamiento=relevamiento,
        estado=PrimerSeguimiento.ESTADO_ASIGNADO,
    )

    with pytest.raises(DjangoValidationError):
        PrimerSeguimientoService.create_asignado(
            comedor.id,
            _territorial_payload(),
        )


def test_build_payload_primer_seguimiento(comedor):
    relevamiento = Relevamiento.objects.create(comedor=comedor, estado="En Proceso")
    seguimiento = PrimerSeguimiento.objects.create(
        id_relevamiento=relevamiento,
        tecnico="uid-1",
        estado=PrimerSeguimiento.ESTADO_ASIGNADO,
    )

    payload = build_primer_seguimiento_payload(seguimiento)

    row = payload["Rows"][0]
    assert payload["Action"] == "Add"
    assert row["ID_Seguimiento1"] == str(seguimiento.id)
    assert row["Id_Relevamiento"] == str(relevamiento.id)
    assert row["CodPNUD"] == "PNUD-001"
    assert row["tecnico"] == "uid-1"


def test_api_primer_seguimiento_exige_ids(api_client):
    response = api_client.patch(
        reverse("api_primer_seguimiento"),
        {"estado": "Completo"},
        format="json",
    )

    assert response.status_code == 400


def test_api_primer_seguimiento_rechaza_ids_inconsistentes(api_client, comedor):
    relevamiento = Relevamiento.objects.create(comedor=comedor, estado="En Proceso")
    otro_relevamiento = Relevamiento.objects.create(comedor=comedor, estado="Pendiente")
    seguimiento = PrimerSeguimiento.objects.create(
        id_relevamiento=relevamiento,
        estado=PrimerSeguimiento.ESTADO_ASIGNADO,
    )

    response = api_client.patch(
        reverse("api_primer_seguimiento"),
        {
            "sisoc_id": seguimiento.id,
            "id_relevamiento": otro_relevamiento.id,
            "estado": "Completo",
        },
        format="json",
    )

    assert response.status_code == 400


def test_api_primer_seguimiento_no_encontrado(api_client, comedor):
    relevamiento = Relevamiento.objects.create(comedor=comedor, estado="En Proceso")

    response = api_client.patch(
        reverse("api_primer_seguimiento"),
        {
            "sisoc_id": 999999,
            "id_relevamiento": relevamiento.id,
            "estado": "Completo",
        },
        format="json",
    )

    assert response.status_code == 404


def test_api_primer_seguimiento_actualiza_bloques_y_estado(api_client, comedor):
    relevamiento = Relevamiento.objects.create(comedor=comedor, estado="En Proceso")
    seguimiento = PrimerSeguimiento.objects.create(
        id_relevamiento=relevamiento,
        estado=PrimerSeguimiento.ESTADO_ASIGNADO,
    )

    response = api_client.patch(
        reverse("api_primer_seguimiento"),
        {
            "sisoc_id": seguimiento.id,
            "id_relevamiento": relevamiento.id,
            "fecha_hora": "2026-04-27T10:30:00-03:00",
            "estado": "Completo",
            "funcionamiento": "Abierto en funcionamiento",
            "agua_potable": "Y",
            "gas_red": "4",
            "observan_animales": "N",
            "prestaciones_seguimientos": {
                "id_prestacion_seg": "prest-1",
                "dias_prestacion": "Lunes",
                "tipo_prestacion": "Almuerzo",
                "ap_presencial": "10",
                "ap_vianda": "2",
                "de_presencial": "3",
                "de_vianda": "4",
            },
            "info_adicional": "Sin novedades",
            "realizo_forma": "Completa",
            "comentarios_finales": "Formulario completo",
            "firma_entrevistado": "https://gestionar.test/firma1.png",
            "firma_tecnico": "https://gestionar.test/firma2.png",
        },
        format="json",
    )

    assert response.status_code == 200
    seguimiento.refresh_from_db()
    assert seguimiento.estado == PrimerSeguimiento.ESTADO_COMPLETO
    assert seguimiento.funcionamiento.funcionamiento == "Abierto en funcionamiento"
    assert seguimiento.servicios_basicos.agua_potable is True
    assert seguimiento.servicios_basicos.gas_red == 4
    assert seguimiento.servicios_basicos.observan_animales is False
    assert seguimiento.prestaciones.get(id_prestacion_seg="prest-1").ap_presencial == 10
    assert seguimiento.cierre.info_adicional == "Sin novedades"


def test_api_primer_seguimiento_hace_rollback_si_bloque_es_invalido(
    api_client,
    comedor,
):
    relevamiento = Relevamiento.objects.create(comedor=comedor, estado="En Proceso")
    seguimiento = PrimerSeguimiento.objects.create(
        id_relevamiento=relevamiento,
        estado=PrimerSeguimiento.ESTADO_ASIGNADO,
    )

    response = api_client.patch(
        reverse("api_primer_seguimiento"),
        {
            "sisoc_id": seguimiento.id,
            "id_relevamiento": relevamiento.id,
            "estado": "Completo",
            "gas_red": "7",
        },
        format="json",
    )

    assert response.status_code == 400
    seguimiento.refresh_from_db()
    assert seguimiento.estado == PrimerSeguimiento.ESTADO_ASIGNADO
    assert seguimiento.servicios_basicos_id is None
