"""Tests del guard de entrada de PATCH /api/relevamiento."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from rest_framework_api_key.models import APIKey

from comedores.models import Comedor
from core.models import Provincia
from relevamientos.models import PrimerSeguimiento, Relevamiento
from users.models import AccesoComedorPWA, TerritorialComedorProvincia


def _token_client(user):
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


def _make_territorial(username, provincias):
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="testpass123",
    )
    user.profile.es_territorial_comedor = True
    user.profile.save(update_fields=["es_territorial_comedor"])
    for provincia in provincias:
        TerritorialComedorProvincia.objects.create(
            profile=user.profile,
            provincia=provincia,
        )
    return user


@pytest.mark.django_db
def test_patch_relevamiento_missing_sisoc_id_returns_400():
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username="patcher",
        email="patcher@example.com",
        password="testpass123",
    )
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    response = client.patch("/api/relevamiento", {}, format="json")

    assert response.status_code == 400


@pytest.mark.django_db
def test_patch_relevamiento_unknown_sisoc_id_returns_404():
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username="patcher2",
        email="patcher2@example.com",
        password="testpass123",
    )
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    response = client.patch("/api/relevamiento", {"sisoc_id": 999999}, format="json")

    assert response.status_code == 404


@pytest.mark.django_db
def test_territorial_patch_relevamiento_inside_scope_is_allowed():
    provincia = Provincia.objects.create(nombre="Provincia permitida")
    comedor = Comedor.objects.create(nombre="Comedor permitido", provincia=provincia)
    relevamiento = Relevamiento.objects.create(comedor=comedor, estado="Pendiente")
    client = _token_client(_make_territorial("territorial_permitido", [provincia]))

    response = client.patch(
        "/api/relevamiento",
        {"sisoc_id": relevamiento.id, "estado": "Finalizado"},
        format="json",
    )

    assert response.status_code == 200
    relevamiento.refresh_from_db()
    assert relevamiento.estado == "Finalizado"
    assert relevamiento.sincronizado_gestionar is True


@pytest.mark.django_db
def test_territorial_puede_finalizar_relevamiento_asignado_fuera_de_su_provincia():
    # El territorial ve (y por lo tanto puede finalizar) lo asignado a él aunque
    # el comedor sea de una provincia que no tiene cargada. Antes esto devolvía
    # 404 porque el scope del PATCH era solo por provincia ("no permite finalizar").
    provincia_cargada = Provincia.objects.create(nombre="Provincia cargada")
    provincia_del_comedor = Provincia.objects.create(nombre="Provincia del comedor")
    comedor = Comedor.objects.create(
        nombre="Comedor asignado", provincia=provincia_del_comedor
    )
    user = _make_territorial("territorial_asignado", [provincia_cargada])
    relevamiento = Relevamiento.objects.create(
        comedor=comedor, estado="Visita pendiente", territorial_user=user
    )

    response = _token_client(user).patch(
        "/api/relevamiento",
        {"sisoc_id": relevamiento.id, "estado": "Finalizado"},
        format="json",
    )

    assert response.status_code == 200
    relevamiento.refresh_from_db()
    assert relevamiento.estado == "Finalizado"


@pytest.mark.django_db
def test_territorial_patch_relevamiento_outside_scope_returns_404_without_mutation():
    provincia_permitida = Provincia.objects.create(nombre="Provincia permitida")
    provincia_ajena = Provincia.objects.create(nombre="Provincia ajena")
    comedor_ajeno = Comedor.objects.create(
        nombre="Comedor ajeno",
        provincia=provincia_ajena,
    )
    relevamiento = Relevamiento.objects.create(
        comedor=comedor_ajeno, estado="Pendiente"
    )
    client = _token_client(
        _make_territorial("territorial_sin_acceso", [provincia_permitida])
    )

    response = client.patch(
        "/api/relevamiento",
        {"sisoc_id": relevamiento.id, "estado": "Finalizado"},
        format="json",
    )

    assert response.status_code == 404
    relevamiento.refresh_from_db()
    assert relevamiento.estado == "Pendiente"
    assert relevamiento.sincronizado_gestionar is False


@pytest.mark.django_db
def test_territorial_patch_primer_seguimiento_inside_scope_is_allowed():
    provincia = Provincia.objects.create(nombre="Provincia seguimiento permitida")
    comedor = Comedor.objects.create(
        nombre="Comedor seguimiento permitido",
        provincia=provincia,
    )
    relevamiento = Relevamiento.objects.create(comedor=comedor, estado="Pendiente")
    seguimiento = PrimerSeguimiento.objects.create(
        id_relevamiento=relevamiento,
        estado=PrimerSeguimiento.ESTADO_ASIGNADO,
    )
    client = _token_client(
        _make_territorial("territorial_seguimiento_permitido", [provincia])
    )

    response = client.patch(
        "/api/relevamiento/primer-seguimiento",
        {"sisoc_id": seguimiento.id, "estado": PrimerSeguimiento.ESTADO_COMPLETO},
        format="json",
    )

    assert response.status_code == 200
    seguimiento.refresh_from_db()
    assert seguimiento.estado == PrimerSeguimiento.ESTADO_COMPLETO
    assert seguimiento.sincronizado_gestionar is True


@pytest.mark.django_db
@pytest.mark.parametrize("identifier", ["sisoc_id", "gestionar_id", "id_relevamiento"])
def test_territorial_patch_primer_seguimiento_outside_scope_returns_404_without_mutation(
    identifier,
):
    provincia_permitida = Provincia.objects.create(nombre="Provincia seguimiento")
    provincia_ajena = Provincia.objects.create(nombre="Provincia seguimiento ajena")
    comedor_ajeno = Comedor.objects.create(
        nombre="Comedor seguimiento ajeno",
        provincia=provincia_ajena,
    )
    relevamiento = Relevamiento.objects.create(
        comedor=comedor_ajeno, estado="Pendiente"
    )
    seguimiento = PrimerSeguimiento.objects.create(
        id_relevamiento=relevamiento,
        estado=PrimerSeguimiento.ESTADO_ASIGNADO,
        gestionar_id="seguimiento-externo",
    )
    client = _token_client(
        _make_territorial("territorial_seguimiento", [provincia_permitida])
    )
    payload = {
        "sisoc_id": seguimiento.id,
        "gestionar_id": seguimiento.gestionar_id,
        "id_relevamiento": relevamiento.id,
    }

    response = client.patch(
        "/api/relevamiento/primer-seguimiento",
        {identifier: payload[identifier], "estado": PrimerSeguimiento.ESTADO_COMPLETO},
        format="json",
    )

    assert response.status_code == 404
    seguimiento.refresh_from_db()
    assert seguimiento.estado == PrimerSeguimiento.ESTADO_ASIGNADO
    assert seguimiento.sincronizado_gestionar is False


@pytest.mark.django_db
def test_authenticated_non_territorial_token_cannot_patch_existing_relevamiento():
    provincia = Provincia.objects.create(nombre="Provincia sin rol")
    comedor = Comedor.objects.create(nombre="Comedor sin rol", provincia=provincia)
    relevamiento = Relevamiento.objects.create(comedor=comedor, estado="Pendiente")
    user = get_user_model().objects.create_user(
        username="usuario_sin_rol",
        email="usuario_sin_rol@example.com",
        password="testpass123",
    )

    response = _token_client(user).patch(
        "/api/relevamiento",
        {"sisoc_id": relevamiento.id, "estado": "Finalizado"},
        format="json",
    )

    assert response.status_code == 404
    relevamiento.refresh_from_db()
    assert relevamiento.estado == "Pendiente"


@pytest.mark.django_db
def test_pwa_representative_token_cannot_patch_existing_relevamiento():
    provincia = Provincia.objects.create(nombre="Provincia representante")
    comedor = Comedor.objects.create(
        nombre="Comedor representante", provincia=provincia
    )
    relevamiento = Relevamiento.objects.create(comedor=comedor, estado="Pendiente")
    representante = get_user_model().objects.create_user(
        username="representante_pwa",
        email="representante_pwa@example.com",
        password="testpass123",
    )
    AccesoComedorPWA.objects.create(
        user=representante,
        comedor=comedor,
        rol=AccesoComedorPWA.ROL_REPRESENTANTE,
    )

    response = _token_client(representante).patch(
        "/api/relevamiento",
        {"sisoc_id": relevamiento.id, "estado": "Finalizado"},
        format="json",
    )

    assert response.status_code == 404
    relevamiento.refresh_from_db()
    assert relevamiento.estado == "Pendiente"


@pytest.mark.django_db
def test_web_session_cannot_patch_existing_relevamiento(client):
    provincia = Provincia.objects.create(nombre="Provincia sesion")
    comedor = Comedor.objects.create(nombre="Comedor sesion", provincia=provincia)
    relevamiento = Relevamiento.objects.create(comedor=comedor, estado="Pendiente")
    user = get_user_model().objects.create_user(
        username="usuario_sesion",
        email="usuario_sesion@example.com",
        password="testpass123",
    )
    client.force_login(user)

    response = client.patch(
        "/api/relevamiento",
        {"sisoc_id": relevamiento.id, "estado": "Finalizado"},
        content_type="application/json",
    )

    assert response.status_code == 404
    relevamiento.refresh_from_db()
    assert relevamiento.estado == "Pendiente"


@pytest.mark.django_db
@pytest.mark.parametrize("header_name", ["HTTP_AUTHORIZATION", "HTTP_API_KEY"])
def test_api_key_can_patch_relevamiento_and_primer_seguimiento(header_name):
    provincia = Provincia.objects.create(nombre="Provincia integracion")
    comedor = Comedor.objects.create(nombre="Comedor integracion", provincia=provincia)
    relevamiento = Relevamiento.objects.create(comedor=comedor, estado="Pendiente")
    seguimiento = PrimerSeguimiento.objects.create(
        id_relevamiento=relevamiento,
        estado=PrimerSeguimiento.ESTADO_ASIGNADO,
    )
    _, key = APIKey.objects.create_key(name="gestionar-tests")
    client = APIClient()
    credentials = (
        {header_name: f"Api-Key {key}"}
        if header_name == "HTTP_AUTHORIZATION"
        else {header_name: key}
    )
    client.credentials(**credentials)

    relevamiento_response = client.patch(
        "/api/relevamiento",
        {"sisoc_id": relevamiento.id, "estado": "Finalizado"},
        format="json",
    )
    seguimiento_response = client.patch(
        "/api/relevamiento/primer-seguimiento",
        {"sisoc_id": seguimiento.id, "estado": PrimerSeguimiento.ESTADO_COMPLETO},
        format="json",
    )

    assert relevamiento_response.status_code == 200
    assert seguimiento_response.status_code == 200
    relevamiento.refresh_from_db()
    seguimiento.refresh_from_db()
    assert relevamiento.estado == "Finalizado"
    assert seguimiento.estado == PrimerSeguimiento.ESTADO_COMPLETO
