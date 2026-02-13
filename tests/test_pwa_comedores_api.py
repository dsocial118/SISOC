import pytest
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from comedores.models import Comedor, Nomina
from core.models import Provincia
from users.models import AccesoComedorPWA


@pytest.fixture
def comedores(db):
    provincia = Provincia.objects.create(nombre="Cordoba")
    comedor_1 = Comedor.objects.create(nombre="Comedor Uno", provincia=provincia)
    comedor_2 = Comedor.objects.create(nombre="Comedor Dos", provincia=provincia)
    return comedor_1, comedor_2


def _create_pwa_user(
    *,
    comedor,
    role,
    username,
    created_by=None,
    password="testpass123",
):
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password=password,
    )
    AccesoComedorPWA.objects.create(
        user=user,
        comedor=comedor,
        rol=role,
        creado_por=created_by,
        activo=True,
    )
    return user


def _token_client(user):
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


@pytest.mark.django_db
def test_comedor_api_requires_authentication(comedores):
    comedor_1, _ = comedores
    client = APIClient()
    response = client.get(f"/api/comedores/{comedor_1.id}/")
    assert response.status_code == 401


@pytest.mark.django_db
def test_comedor_api_accepts_non_pwa_token(comedores):
    comedor_1, _ = comedores
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username="no_pwa",
        email="no_pwa@example.com",
        password="testpass123",
    )
    client = _token_client(user)
    response = client.get(f"/api/comedores/{comedor_1.id}/")
    assert response.status_code == 200
    assert response.data["id"] == comedor_1.id


@pytest.mark.django_db
def test_representante_scope_returns_404_for_unassigned_comedor(comedores):
    comedor_1, comedor_2 = comedores
    representante = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_scope",
    )
    client = _token_client(representante)

    ok_response = client.get(f"/api/comedores/{comedor_1.id}/")
    forbidden_scope_response = client.get(f"/api/comedores/{comedor_2.id}/")

    assert ok_response.status_code == 200
    assert forbidden_scope_response.status_code == 404


@pytest.mark.django_db
def test_representante_can_list_and_create_operadores(comedores):
    comedor_1, _ = comedores
    representante = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_users",
    )
    operador_existente = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_OPERADOR,
        username="op_existente",
        created_by=representante,
    )
    client = _token_client(representante)

    list_response = client.get(f"/api/comedores/{comedor_1.id}/usuarios/")
    assert list_response.status_code == 200
    assert list_response.data["count"] == 1
    assert list_response.data["results"][0]["id"] == operador_existente.id

    create_response = client.post(
        f"/api/comedores/{comedor_1.id}/usuarios/",
        {
            "username": "op_nuevo",
            "email": "op_nuevo@example.com",
            "password": "Secreta123!",
        },
        format="json",
    )
    assert create_response.status_code == 201
    assert create_response.data["username"] == "op_nuevo"
    assert create_response.data["rol"] == AccesoComedorPWA.ROL_OPERADOR


@pytest.mark.django_db
def test_operador_cannot_manage_users_endpoint(comedores):
    comedor_1, _ = comedores
    representante = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_creador",
    )
    operador = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_OPERADOR,
        username="op_solo",
        created_by=representante,
    )
    client = _token_client(operador)

    get_response = client.get(f"/api/comedores/{comedor_1.id}/usuarios/")
    post_response = client.post(
        f"/api/comedores/{comedor_1.id}/usuarios/",
        {"username": "otro", "email": "otro@example.com", "password": "Secreta123!"},
        format="json",
    )

    assert get_response.status_code == 403
    assert post_response.status_code == 403


@pytest.mark.django_db
def test_representante_can_deactivate_operador(comedores):
    comedor_1, _ = comedores
    representante = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_deact",
    )
    operador = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_OPERADOR,
        username="op_deact",
        created_by=representante,
    )
    client = _token_client(representante)

    response = client.patch(
        f"/api/comedores/{comedor_1.id}/usuarios/{operador.id}/desactivar/",
        {},
        format="json",
    )

    assert response.status_code == 200
    operador.refresh_from_db()
    acceso = AccesoComedorPWA.objects.get(user=operador, comedor=comedor_1)
    assert operador.is_active is False
    assert acceso.activo is False


@pytest.mark.django_db
def test_cualquier_representante_del_mismo_comedor_puede_desactivar(comedores):
    comedor_1, _ = comedores
    representante_1 = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_a",
    )
    representante_2 = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_b",
    )
    operador = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_OPERADOR,
        username="op_multi_rep",
        created_by=representante_1,
    )
    client = _token_client(representante_2)

    response = client.patch(
        f"/api/comedores/{comedor_1.id}/usuarios/{operador.id}/desactivar/",
        {},
        format="json",
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_nomina_scope_is_filtered_by_pwa_access(comedores):
    comedor_1, comedor_2 = comedores
    representante = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_nomina",
    )
    client = _token_client(representante)

    nomina_asignada = Nomina.objects.create(comedor=comedor_1)
    nomina_fuera_scope = Nomina.objects.create(comedor=comedor_2)

    ok_response = client.patch(
        f"/api/comedores/nomina/{nomina_asignada.id}/",
        {"estado": "activo"},
        format="json",
    )
    forbidden_scope_response = client.patch(
        f"/api/comedores/nomina/{nomina_fuera_scope.id}/",
        {"estado": "activo"},
        format="json",
    )

    assert ok_response.status_code == 200
    assert forbidden_scope_response.status_code == 404
