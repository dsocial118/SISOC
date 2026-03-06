import pytest
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from comedores.models import Comedor
from core.models import Provincia
from pwa.models import AuditoriaOperacionPWA, ColaboradorEspacioPWA
from users.models import AccesoComedorPWA


@pytest.fixture
def comedor(db):
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    return Comedor.objects.create(nombre="Comedor Colaboradores", provincia=provincia)


def _create_representante(*, comedor, username="rep_colab", password="testpass123"):
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password=password,
    )
    AccesoComedorPWA.objects.create(
        user=user,
        comedor=comedor,
        rol=AccesoComedorPWA.ROL_REPRESENTANTE,
        activo=True,
    )
    return user


def _auth_client_for_user(user):
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


@pytest.mark.django_db
def test_create_colaborador_ok(comedor):
    representante = _create_representante(comedor=comedor)
    client = _auth_client_for_user(representante)

    response = client.post(
        f"/api/pwa/espacios/{comedor.id}/colaboradores/",
        {
            "nombre": "Ana",
            "apellido": "Gomez",
            "dni": "12345678",
            "telefono": "+54 11 1234 5678",
            "email": "ana@example.com",
            "rol_funcion": "Cocinera",
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.data["nombre"] == "Ana"
    colaborador_id = response.data["id"]
    assert ColaboradorEspacioPWA.objects.filter(
        comedor=comedor,
        dni="12345678",
        activo=True,
    ).exists()
    assert AuditoriaOperacionPWA.objects.filter(
        entidad="colaborador",
        entidad_id=colaborador_id,
        accion="create",
    ).exists()


@pytest.mark.django_db
def test_create_colaborador_rechaza_dni_duplicado_en_mismo_espacio(comedor):
    representante = _create_representante(comedor=comedor)
    client = _auth_client_for_user(representante)
    ColaboradorEspacioPWA.objects.create(
        comedor=comedor,
        nombre="Ana",
        apellido="Gomez",
        dni="12345678",
        telefono="11111111",
        email="ana@example.com",
        rol_funcion="Cocinera",
        creado_por=representante,
        actualizado_por=representante,
    )

    response = client.post(
        f"/api/pwa/espacios/{comedor.id}/colaboradores/",
        {
            "nombre": "Otra",
            "apellido": "Persona",
            "dni": "12345678",
            "telefono": "22222222",
            "email": "otra@example.com",
            "rol_funcion": "Ayudante",
        },
        format="json",
    )

    assert response.status_code == 400
    assert "dni" in response.data


@pytest.mark.django_db
def test_create_colaborador_valida_formatos(comedor):
    representante = _create_representante(comedor=comedor)
    client = _auth_client_for_user(representante)

    response = client.post(
        f"/api/pwa/espacios/{comedor.id}/colaboradores/",
        {
            "nombre": "Ana",
            "apellido": "Gomez",
            "dni": "12A",
            "telefono": "telefono-invalido***",
            "email": "mail-invalido",
            "rol_funcion": "Cocinera",
        },
        format="json",
    )

    assert response.status_code == 400
    assert "dni" in response.data
    assert "telefono" in response.data
    assert "email" in response.data


@pytest.mark.django_db
def test_update_colaborador_ok(comedor):
    representante = _create_representante(comedor=comedor)
    client = _auth_client_for_user(representante)
    colaborador = ColaboradorEspacioPWA.objects.create(
        comedor=comedor,
        nombre="Ana",
        apellido="Gomez",
        dni="12345678",
        telefono="11111111",
        email="ana@example.com",
        rol_funcion="Cocinera",
        creado_por=representante,
        actualizado_por=representante,
    )

    response = client.patch(
        f"/api/pwa/espacios/{comedor.id}/colaboradores/{colaborador.id}/",
        {
            "telefono": "+54 9 11 5555 9999",
            "rol_funcion": "Encargada",
        },
        format="json",
    )

    assert response.status_code == 200
    colaborador.refresh_from_db()
    assert colaborador.telefono == "+54 9 11 5555 9999"
    assert colaborador.rol_funcion == "Encargada"
    assert AuditoriaOperacionPWA.objects.filter(
        entidad="colaborador",
        entidad_id=colaborador.id,
        accion="update",
    ).exists()


@pytest.mark.django_db
def test_delete_colaborador_es_baja_logica(comedor):
    representante = _create_representante(comedor=comedor)
    client = _auth_client_for_user(representante)
    colaborador = ColaboradorEspacioPWA.objects.create(
        comedor=comedor,
        nombre="Ana",
        apellido="Gomez",
        dni="12345678",
        telefono="11111111",
        email="ana@example.com",
        rol_funcion="Cocinera",
        creado_por=representante,
        actualizado_por=representante,
    )

    response = client.delete(
        f"/api/pwa/espacios/{comedor.id}/colaboradores/{colaborador.id}/",
    )

    assert response.status_code == 204
    colaborador.refresh_from_db()
    assert colaborador.activo is False
    assert colaborador.fecha_baja is not None
    assert AuditoriaOperacionPWA.objects.filter(
        entidad="colaborador",
        entidad_id=colaborador.id,
        accion="delete",
    ).exists()


@pytest.mark.django_db
def test_colaboradores_requiere_representante_del_espacio(comedor):
    user_model = get_user_model()
    other_user = user_model.objects.create_user(
        username="sin_permiso_colab",
        email="sin_permiso_colab@example.com",
        password="testpass123",
    )
    client = _auth_client_for_user(other_user)

    response = client.get(f"/api/pwa/espacios/{comedor.id}/colaboradores/")

    assert response.status_code == 403
