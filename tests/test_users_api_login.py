"""Tests for test users api login."""

import pytest
from django.contrib.auth import SESSION_KEY, get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from comedores.models import Comedor
from core.models import Provincia
from users.models import AccesoComedorPWA


@pytest.fixture
def comedor(db):
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    return Comedor.objects.create(nombre="Comedor Test", provincia=provincia)


def _create_representante(*, comedor, username="rep_user", password="testpass123"):
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
def test_api_login_returns_token_for_pwa_user(comedor):
    user = _create_representante(comedor=comedor)
    client = APIClient()

    response = client.post(
        "/api/users/login/",
        {"username": "rep_user", "password": "testpass123"},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["token_type"] == "Token"
    assert Token.objects.filter(user=user, key=response.data["token"]).exists()


@pytest.mark.django_db
def test_api_login_rejects_invalid_credentials(comedor):
    _create_representante(comedor=comedor)
    client = APIClient()

    response = client.post(
        "/api/users/login/",
        {"username": "rep_user", "password": "wrongpass"},
        format="json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_api_login_rejects_non_pwa_user():
    user_model = get_user_model()
    user_model.objects.create_user(
        username="api_user",
        email="api_user@example.com",
        password="testpass123",
    )
    client = APIClient()

    response = client.post(
        "/api/users/login/",
        {"username": "api_user", "password": "testpass123"},
        format="json",
    )

    assert response.status_code == 401
    assert response.data["detail"] == "Este usuario no tiene acceso PWA activo."


@pytest.mark.django_db
def test_users_me_requires_authentication():
    client = APIClient()
    response = client.get("/api/users/me/")
    assert response.status_code == 401


@pytest.mark.django_db
def test_users_me_accepts_non_pwa_token():
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username="api_user",
        email="api_user@example.com",
        password="testpass123",
    )
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    response = client.get("/api/users/me/")

    assert response.status_code == 200
    assert response.data["pwa"]["is_pwa_user"] is False


@pytest.mark.django_db
def test_users_me_with_pwa_token_includes_pwa_context(comedor):
    user = _create_representante(comedor=comedor)
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    response = client.get("/api/users/me/")

    assert response.status_code == 200
    assert response.data["id"] == user.id
    assert response.data["pwa"]["is_pwa_user"] is True
    assert response.data["pwa"]["roles"] == ["representante"]
    assert response.data["pwa"]["comedores_representados"] == [comedor.id]
    assert response.data["pwa"]["comedor_operador_id"] is None


@pytest.mark.django_db
def test_users_logout_requires_token():
    client = APIClient()

    response = client.post("/api/users/logout/", {}, format="json")

    assert response.status_code == 401


@pytest.mark.django_db
def test_users_logout_accepts_non_pwa_token():
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username="api_user",
        email="api_user@example.com",
        password="testpass123",
    )
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    response = client.post("/api/users/logout/", {}, format="json")

    assert response.status_code == 200
    assert Token.objects.filter(key=token.key).exists() is False


@pytest.mark.django_db
def test_users_logout_invalidates_token_for_pwa_user(comedor):
    user = _create_representante(comedor=comedor)
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    logout_response = client.post("/api/users/logout/", {}, format="json")

    assert logout_response.status_code == 200
    assert Token.objects.filter(key=token.key).exists() is False

    me_response = client.get("/api/users/me/")
    assert me_response.status_code == 401


@pytest.mark.django_db
def test_web_login_blocks_pwa_user(client, comedor):
    _create_representante(comedor=comedor, username="rep_web", password="testpass123")

    response = client.post(
        "/login/",
        data={"username": "rep_web", "password": "testpass123"},
    )

    assert response.status_code == 200
    assert SESSION_KEY not in client.session


@pytest.mark.django_db
def test_password_change_required_requires_authentication():
    client = APIClient()

    response = client.post(
        "/api/users/password-change-required/",
        {"new_password": "NuevaClave123!"},
        format="json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_password_change_required_updates_password_and_clears_flags(comedor):
    user = _create_representante(
        comedor=comedor,
        username="rep_pwd_change",
        password="Temporal123!",
    )
    user.profile.must_change_password = True
    user.profile.temporary_password_plaintext = "Temporal123!"
    user.profile.save(
        update_fields=["must_change_password", "temporary_password_plaintext"]
    )
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    response = client.post(
        "/api/users/password-change-required/",
        {"new_password": "NuevaClave123!"},
        format="json",
    )

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.check_password("NuevaClave123!") is True
    assert user.profile.must_change_password is False
    assert user.profile.temporary_password_plaintext is None


@pytest.mark.django_db
def test_password_change_required_rejects_when_not_needed(comedor):
    user = _create_representante(
        comedor=comedor,
        username="rep_pwd_ok",
        password="ClaveActual123!",
    )
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    response = client.post(
        "/api/users/password-change-required/",
        {"new_password": "NuevaClave123!"},
        format="json",
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_password_change_required_validates_new_password(comedor):
    user = _create_representante(
        comedor=comedor,
        username="rep_pwd_invalid",
        password="Temporal123!",
    )
    user.profile.must_change_password = True
    user.profile.save(update_fields=["must_change_password"])
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    response = client.post(
        "/api/users/password-change-required/",
        {"new_password": "123"},
        format="json",
    )

    assert response.status_code == 400
    assert "new_password" in response.data
