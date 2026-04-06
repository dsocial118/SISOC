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
def test_web_login_treats_whitespace_only_fields_as_required(client):
    response = client.post(
        "/login/",
        data={"username": "   ", "password": "   "},
    )

    assert response.status_code == 200
    assert SESSION_KEY not in client.session
    assert response.context["form"].errors["username"] == ["Este campo es obligatorio."]
    assert response.context["form"].errors["password"] == ["Este campo es obligatorio."]


@pytest.mark.django_db
def test_login_page_sets_initial_focus_on_username(client):
    response = client.get("/login/")

    assert response.status_code == 200
    assert 'id="id_username"' in response.content.decode("utf-8")
    assert "autofocus" in response.content.decode("utf-8")


@pytest.mark.django_db
def test_login_page_renders_loading_submit_button(client):
    response = client.get("/login/")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert 'id="login-submit-button"' in content
    assert 'id="login-submit-spinner"' in content
    assert "spinner-border" in content
    assert 'id="login-submit-text"' in content
    assert ">Ingresar<" in content


@pytest.mark.django_db
def test_web_login_allows_valid_username_with_leading_spaces(client):
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username="usuario_valido",
        email="usuario_valido@example.com",
        password="ClaveValida123!",
    )

    response = client.post(
        "/login/",
        data={"username": "   usuario_valido", "password": "ClaveValida123!"},
    )

    assert response.status_code in {302, 303}
    assert client.session[SESSION_KEY] == str(user.pk)


@pytest.mark.django_db
def test_web_login_shows_generic_message_for_invalid_credentials(client):
    response = client.post(
        "/login/",
        data={"username": "usuario_invalido", "password": "clave_invalida"},
    )

    assert response.status_code == 200
    assert SESSION_KEY not in client.session
    assert response.context["form"].non_field_errors() == [
        "Usuario o contraseña inválidos."
    ]


@pytest.mark.django_db
def test_web_login_preserves_username_and_clears_password_after_failed_login(client):
    response = client.post(
        "/login/",
        data={"username": "usuario_invalido", "password": "clave_invalida"},
    )

    assert response.status_code == 200
    assert response.context["form"]["username"].value() == "usuario_invalido"
    assert response.context["form"]["password"].value() in (None, "")
    content = response.content.decode("utf-8")
    assert 'value="usuario_invalido"' in content
    assert 'name="password"' in content
    assert 'value="clave_invalida"' not in content


@pytest.mark.django_db
def test_web_login_keeps_significant_password_spaces(client):
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username="usuario_con_password_espaciado",
        email="usuario_con_password_espaciado@example.com",
        password="  ClaveValida123!",
    )

    response = client.post(
        "/login/",
        data={
            "username": "usuario_con_password_espaciado",
            "password": "  ClaveValida123!",
        },
    )

    assert response.status_code in {302, 303}
    assert client.session[SESSION_KEY] == str(user.pk)


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
