"""Tests for primer seguimiento de relevamiento de comedor."""

import json

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.urls import reverse

from comedores.models import Comedor, Referente
from relevamientos.models import (
    CierreSeguimiento,
    FuncionamientoSeguimiento,
    PrestacionSeguimiento,
    PrimerSeguimiento,
    Relevamiento,
    ServiciosBasicosSeguimiento,
)
from relevamientos.primer_seguimiento_service import PrimerSeguimientoService
from relevamientos.tasks import (
    AsyncRemovePrimerSeguimientoToGestionar,
    AsyncSendPrimerSeguimientoToGestionar,
    build_primer_seguimiento_payload,
)


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

    assert payload["Action"] == "Add"
    assert payload["Properties"] == {"Locale": "es-ES"}
    assert payload["Rows"] == [
        {
            "ID_Seguimiento1": str(seguimiento.id),
            "Id_Relevamiento": str(relevamiento.id),
            "Id_SISOC": str(seguimiento.id),
        }
    ]


def test_async_send_guarda_gestionar_id_de_la_respuesta(comedor, mocker, settings):
    settings.GESTIONAR_INTEGRATION_ENABLED = True
    relevamiento = Relevamiento.objects.create(comedor=comedor, estado="En Proceso")
    seguimiento = PrimerSeguimiento.objects.create(
        id_relevamiento=relevamiento,
        estado=PrimerSeguimiento.ESTADO_ASIGNADO,
    )

    response = mocker.Mock()
    response.raise_for_status.return_value = None
    response.content = b'{"Rows": [{"ID_Seguimiento1": "afbeaa6c"}]}'
    response.json.return_value = {"Rows": [{"ID_Seguimiento1": "afbeaa6c"}]}
    mocker.patch("relevamientos.tasks.requests.post", return_value=response)

    AsyncSendPrimerSeguimientoToGestionar(
        seguimiento.id,
        build_primer_seguimiento_payload(seguimiento),
    ).run()

    seguimiento.refresh_from_db()
    assert seguimiento.gestionar_id == "afbeaa6c"


def test_async_remove_usa_gestionar_id_y_omite_si_falta(comedor, mocker, settings):
    settings.GESTIONAR_INTEGRATION_ENABLED = True
    relevamiento = Relevamiento.objects.create(comedor=comedor, estado="En Proceso")
    seguimiento = PrimerSeguimiento.objects.create(
        id_relevamiento=relevamiento,
        estado=PrimerSeguimiento.ESTADO_ASIGNADO,
        gestionar_id="afbeaa6c",
    )
    post_mock = mocker.patch("relevamientos.tasks.requests.post")

    AsyncRemovePrimerSeguimientoToGestionar(
        seguimiento.id, seguimiento.gestionar_id
    ).run()

    body_enviado = post_mock.call_args.kwargs["json"]
    assert body_enviado["Action"] == "Delete"
    assert body_enviado["Rows"] == [{"ID_Seguimiento1": "afbeaa6c"}]

    post_mock.reset_mock()
    AsyncRemovePrimerSeguimientoToGestionar(seguimiento.id, "").start()
    post_mock.assert_not_called()


def test_api_primer_seguimiento_exige_algun_identificador(api_client):
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


def test_api_primer_seguimiento_resuelve_por_gestionar_id(api_client, comedor):
    relevamiento = Relevamiento.objects.create(comedor=comedor, estado="En Proceso")
    seguimiento = PrimerSeguimiento.objects.create(
        id_relevamiento=relevamiento,
        estado=PrimerSeguimiento.ESTADO_ASIGNADO,
        gestionar_id="afbeaa6c",
    )

    response = api_client.patch(
        reverse("api_primer_seguimiento"),
        {"ID_Seguimiento1": "afbeaa6c", "estado": "Completo"},
        format="json",
    )

    assert response.status_code == 200
    seguimiento.refresh_from_db()
    assert seguimiento.estado == PrimerSeguimiento.ESTADO_COMPLETO


def test_api_primer_seguimiento_resuelve_por_id_relevamiento(api_client, comedor):
    relevamiento = Relevamiento.objects.create(comedor=comedor, estado="En Proceso")
    seguimiento = PrimerSeguimiento.objects.create(
        id_relevamiento=relevamiento,
        estado=PrimerSeguimiento.ESTADO_ASIGNADO,
    )

    response = api_client.patch(
        reverse("api_primer_seguimiento"),
        {"Id_Relevamiento": relevamiento.id, "estado": "Completo"},
        format="json",
    )

    assert response.status_code == 200
    seguimiento.refresh_from_db()
    assert seguimiento.estado == PrimerSeguimiento.ESTADO_COMPLETO


def test_api_primer_seguimiento_marca_sincronizado_tras_patch(api_client, comedor):
    relevamiento = Relevamiento.objects.create(comedor=comedor, estado="En Proceso")
    seguimiento = PrimerSeguimiento.objects.create(
        id_relevamiento=relevamiento,
        estado=PrimerSeguimiento.ESTADO_ASIGNADO,
    )
    assert seguimiento.sincronizado_gestionar is False

    response = api_client.patch(
        reverse("api_primer_seguimiento"),
        {
            "sisoc_id": seguimiento.id,
            "id_relevamiento": relevamiento.id,
            "estado": "Completo",
        },
        format="json",
    )

    assert response.status_code == 200
    seguimiento.refresh_from_db()
    assert seguimiento.sincronizado_gestionar is True


def test_api_primer_seguimiento_referente_por_sisoc_id(api_client, comedor):
    relevamiento = Relevamiento.objects.create(comedor=comedor, estado="En Proceso")
    seguimiento = PrimerSeguimiento.objects.create(
        id_relevamiento=relevamiento,
        estado=PrimerSeguimiento.ESTADO_ASIGNADO,
    )
    referente = Referente.objects.create(
        nombre="Ana", apellido="Lopez", documento=30111222
    )

    response = api_client.patch(
        reverse("api_primer_seguimiento"),
        {
            "sisoc_id": seguimiento.id,
            "id_relevamiento": relevamiento.id,
            "referente": {"sisoc_id": referente.id},
        },
        format="json",
    )

    assert response.status_code == 200
    seguimiento.refresh_from_db()
    assert seguimiento.referente_id == referente.id


def test_api_primer_seguimiento_referente_get_or_create_por_documento(
    api_client, comedor
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
            "referente": {
                "documento": "30.555.777",
                "nombre": "Maria",
                "apellido": "Garcia",
                "mail": "maria@test.local",
                "celular": "1144556677",
                "funcion": "Coordinadora",
            },
        },
        format="json",
    )

    assert response.status_code == 200
    referente = Referente.objects.get(documento=30555777)
    assert referente.nombre == "Maria"
    assert referente.apellido == "Garcia"
    seguimiento.refresh_from_db()
    assert seguimiento.referente_id == referente.id

    # Segundo PATCH con el mismo documento actualiza, no crea otro Referente.
    response = api_client.patch(
        reverse("api_primer_seguimiento"),
        {
            "sisoc_id": seguimiento.id,
            "id_relevamiento": relevamiento.id,
            "referente": {"documento": "30555777", "funcion": "Directora"},
        },
        format="json",
    )
    assert response.status_code == 200
    assert Referente.objects.filter(documento=30555777).count() == 1
    referente.refresh_from_db()
    assert referente.funcion == "Directora"
    assert referente.nombre == "Maria"  # no se pisa con None


def test_api_primer_seguimiento_referente_sisoc_id_inexistente(api_client, comedor):
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
            "referente": {"sisoc_id": 999999},
        },
        format="json",
    )

    assert response.status_code == 400


def test_api_primer_seguimiento_rechaza_gestionar_id_inconsistente(api_client, comedor):
    relevamiento = Relevamiento.objects.create(comedor=comedor, estado="En Proceso")
    seguimiento = PrimerSeguimiento.objects.create(
        id_relevamiento=relevamiento,
        estado=PrimerSeguimiento.ESTADO_ASIGNADO,
        gestionar_id="afbeaa6c",
    )

    response = api_client.patch(
        reverse("api_primer_seguimiento"),
        {
            "sisoc_id": seguimiento.id,
            "ID_Seguimiento1": "otro-id",
            "estado": "Completo",
        },
        format="json",
    )

    assert response.status_code == 400


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


def test_detalle_primer_seguimiento_renderiza_bloques(auth_client, comedor):
    relevamiento = Relevamiento.objects.create(comedor=comedor, estado="En Proceso")
    funcionamiento = FuncionamientoSeguimiento.objects.create(
        funcionamiento=FuncionamientoSeguimiento.ABIERTO_FUNCIONANDO,
    )
    servicios = ServiciosBasicosSeguimiento.objects.create(
        agua_potable=True,
        gas_red=3,
        observan_animales=False,
    )
    cierre = CierreSeguimiento.objects.create(
        info_adicional="Sin novedades",
        realizo_forma=CierreSeguimiento.COMPLETA,
        comentarios_finales="Formulario completo",
    )
    seguimiento = PrimerSeguimiento.objects.create(
        id_relevamiento=relevamiento,
        estado=PrimerSeguimiento.ESTADO_COMPLETO,
        tecnico="uid-1",
        funcionamiento=funcionamiento,
        servicios_basicos=servicios,
        cierre=cierre,
    )
    PrestacionSeguimiento.objects.create(
        seguimiento=seguimiento,
        id_prestacion_seg="prest-1",
        dias_prestacion="Lunes",
        tipo_prestacion="Almuerzo",
        ap_presencial=10,
    )

    url = reverse(
        "primer_seguimiento_detalle",
        kwargs={"comedor_pk": comedor.id, "relevamiento_pk": relevamiento.id},
    )
    response = auth_client.get(url)

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "Primer seguimiento" in content
    assert "Funcionamiento" in content
    assert "Abierto en funcionamiento" in content
    assert "Servicios básicos" in content
    assert "Cierre" in content
    assert "Sin novedades" in content
    assert "prest-1" in content


def test_detalle_primer_seguimiento_skippea_bloques_vacios(auth_client, comedor):
    relevamiento = Relevamiento.objects.create(comedor=comedor, estado="En Proceso")
    funcionamiento = FuncionamientoSeguimiento.objects.create(
        funcionamiento=FuncionamientoSeguimiento.ABIERTO_FUNCIONANDO,
    )
    PrimerSeguimiento.objects.create(
        id_relevamiento=relevamiento,
        estado=PrimerSeguimiento.ESTADO_ASIGNADO,
        funcionamiento=funcionamiento,
    )

    url = reverse(
        "primer_seguimiento_detalle",
        kwargs={"comedor_pk": comedor.id, "relevamiento_pk": relevamiento.id},
    )
    response = auth_client.get(url)

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert 'id="bloque-funcionamiento"' in content
    assert 'id="bloque-cierre"' not in content
    assert 'id="bloque-servicios_basicos"' not in content


def test_detalle_primer_seguimiento_404_si_no_existe(auth_client, comedor):
    relevamiento = Relevamiento.objects.create(comedor=comedor, estado="En Proceso")

    url = reverse(
        "primer_seguimiento_detalle",
        kwargs={"comedor_pk": comedor.id, "relevamiento_pk": relevamiento.id},
    )
    response = auth_client.get(url)

    assert response.status_code == 404


def test_detalle_primer_seguimiento_404_si_comedor_no_coincide(auth_client, comedor):
    otro_comedor = Comedor.objects.create(nombre="Otro comedor")
    relevamiento = Relevamiento.objects.create(comedor=comedor, estado="En Proceso")
    PrimerSeguimiento.objects.create(
        id_relevamiento=relevamiento,
        estado=PrimerSeguimiento.ESTADO_ASIGNADO,
    )

    url = reverse(
        "primer_seguimiento_detalle",
        kwargs={"comedor_pk": otro_comedor.id, "relevamiento_pk": relevamiento.id},
    )
    response = auth_client.get(url)

    assert response.status_code == 404


def _crear_seguimiento_con_gestionar_id(comedor, gestionar_id="afbeaa6c"):
    relevamiento = Relevamiento.objects.create(comedor=comedor, estado="En Proceso")
    seguimiento = PrimerSeguimiento.objects.create(
        id_relevamiento=relevamiento,
        estado=PrimerSeguimiento.ESTADO_ASIGNADO,
        gestionar_id=gestionar_id,
    )
    return relevamiento, seguimiento


def test_eliminar_primer_seguimiento_desde_ui_dispara_baja_gestionar(
    client, comedor, mocker
):
    relevamiento, seguimiento = _crear_seguimiento_con_gestionar_id(comedor)

    user_model = get_user_model()
    user = user_model.objects.create_user(username="eliminador", password="testpass")
    user.user_permissions.add(
        Permission.objects.get(codename="delete_primerseguimiento")
    )
    client.force_login(user)

    remove_start = mocker.patch(
        "relevamientos.signals.AsyncRemovePrimerSeguimientoToGestionar.start"
    )

    response = client.post(
        reverse(
            "primer_seguimiento_eliminar",
            kwargs={
                "comedor_pk": comedor.id,
                "relevamiento_pk": relevamiento.id,
            },
        )
    )

    assert response.status_code == 302
    assert response.url == reverse(
        "relevamiento_detalle",
        kwargs={"comedor_pk": comedor.id, "pk": relevamiento.id},
    )
    assert not PrimerSeguimiento.objects.filter(pk=seguimiento.id).exists()
    remove_start.assert_called_once_with()


def test_eliminar_primer_seguimiento_sin_permiso_devuelve_403(client, comedor, mocker):
    relevamiento, seguimiento = _crear_seguimiento_con_gestionar_id(comedor)

    user_model = get_user_model()
    user = user_model.objects.create_user(username="curioso", password="testpass")
    client.force_login(user)

    remove_start = mocker.patch(
        "relevamientos.signals.AsyncRemovePrimerSeguimientoToGestionar.start"
    )

    response = client.post(
        reverse(
            "primer_seguimiento_eliminar",
            kwargs={
                "comedor_pk": comedor.id,
                "relevamiento_pk": relevamiento.id,
            },
        )
    )

    assert response.status_code == 403
    assert PrimerSeguimiento.objects.filter(pk=seguimiento.id).exists()
    remove_start.assert_not_called()
