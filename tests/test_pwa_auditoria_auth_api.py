import pytest
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from comedores.models import Comedor
from core.models import Provincia
from pwa.models import AuditoriaSesionPWA
from users.models import AccesoComedorPWA


@pytest.fixture
def comedor(db):
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    return Comedor.objects.create(nombre="Comedor Auditoria", provincia=provincia)


def _create_representante(*, comedor, username="rep_audit", password="testpass123"):
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


@pytest.mark.django_db
def test_login_ok_registra_auditoria_con_campos_opcionales(comedor):
    user = _create_representante(comedor=comedor)
    client = APIClient()

    response = client.post(
        "/api/users/login/",
        {"username": user.username, "password": "testpass123"},
        format="json",
        HTTP_USER_AGENT="pytest-agent",
        HTTP_X_FORWARDED_FOR="203.0.113.5, 127.0.0.1",
        HTTP_X_APP_VERSION="1.2.3",
        HTTP_X_PLATFORM="android",
        HTTP_X_PWA_STANDALONE="true",
    )

    assert response.status_code == 200
    audit = AuditoriaSesionPWA.objects.get(evento=AuditoriaSesionPWA.EVENTO_LOGIN_OK)
    assert audit.resultado == AuditoriaSesionPWA.RESULTADO_OK
    assert audit.user_id == user.id
    assert audit.username_intentado == user.username
    assert audit.codigo_respuesta == 200
    assert audit.ip == "203.0.113.5"
    assert audit.user_agent == "pytest-agent"
    assert audit.app_version == "1.2.3"
    assert audit.platform == "android"
    assert audit.is_standalone is True
    assert audit.rol_pwa_snapshot == [AccesoComedorPWA.ROL_REPRESENTANTE]
    assert audit.comedor_ids_snapshot == [comedor.id]


@pytest.mark.django_db
def test_login_error_registra_auditoria_sin_usuario():
    user_model = get_user_model()
    user_model.objects.create_user(
        username="usuario_fail",
        email="usuario_fail@example.com",
        password="testpass123",
    )
    client = APIClient()

    response = client.post(
        "/api/users/login/",
        {"username": "usuario_fail", "password": "badpass"},
        format="json",
    )

    assert response.status_code == 401
    audit = AuditoriaSesionPWA.objects.get(evento=AuditoriaSesionPWA.EVENTO_LOGIN_ERROR)
    assert audit.resultado == AuditoriaSesionPWA.RESULTADO_ERROR
    assert audit.user is None
    assert audit.username_intentado == "usuario_fail"
    assert audit.codigo_respuesta == 401
    assert "inválidas" in (audit.motivo_error or "")


@pytest.mark.django_db
def test_me_y_logout_registran_auditoria(comedor):
    user = _create_representante(comedor=comedor, username="usuario_me_logout")
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    me_response = client.get("/api/users/me/")
    logout_response = client.post("/api/users/logout/", {}, format="json")

    assert me_response.status_code == 200
    assert logout_response.status_code == 200
    assert AuditoriaSesionPWA.objects.filter(
        evento=AuditoriaSesionPWA.EVENTO_ME_OK,
        user=user,
        resultado=AuditoriaSesionPWA.RESULTADO_OK,
        codigo_respuesta=200,
    ).exists()
    assert AuditoriaSesionPWA.objects.filter(
        evento=AuditoriaSesionPWA.EVENTO_LOGOUT,
        user=user,
        resultado=AuditoriaSesionPWA.RESULTADO_OK,
        codigo_respuesta=200,
    ).exists()
