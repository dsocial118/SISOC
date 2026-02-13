import pytest
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_api_login_returns_token():
    user_model = get_user_model()
    user = user_model.objects.create_user(
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

    assert response.status_code == 200
    assert response.data["token_type"] == "Token"
    assert Token.objects.filter(user=user, key=response.data["token"]).exists()


@pytest.mark.django_db
def test_api_login_rejects_invalid_credentials():
    user_model = get_user_model()
    user_model.objects.create_user(
        username="api_user",
        email="api_user@example.com",
        password="testpass123",
    )
    client = APIClient()

    response = client.post(
        "/api/users/login/",
        {"username": "api_user", "password": "wrongpass"},
        format="json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_users_me_requires_authentication():
    client = APIClient()

    response = client.get("/api/users/me/")

    assert response.status_code == 401


@pytest.mark.django_db
def test_users_me_with_token_authentication():
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
    assert response.data["id"] == user.id
    assert response.data["username"] == user.username


@pytest.mark.django_db
def test_comedor_api_requires_authentication():
    client = APIClient()

    response = client.get("/api/comedores/1/")

    assert response.status_code == 401


@pytest.mark.django_db
def test_users_me_rejects_session_only_authentication():
    user_model = get_user_model()
    user_model.objects.create_user(
        username="api_user",
        email="api_user@example.com",
        password="testpass123",
    )
    client = APIClient()
    assert client.login(username="api_user", password="testpass123")

    response = client.get("/api/users/me/")

    assert response.status_code == 401


@pytest.mark.django_db
def test_users_logout_requires_token():
    client = APIClient()

    response = client.post("/api/users/logout/", {}, format="json")

    assert response.status_code == 401


@pytest.mark.django_db
def test_users_logout_invalidates_token():
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username="api_user",
        email="api_user@example.com",
        password="testpass123",
    )
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    logout_response = client.post("/api/users/logout/", {}, format="json")

    assert logout_response.status_code == 200
    assert Token.objects.filter(key=token.key).exists() is False

    me_response = client.get("/api/users/me/")

    assert me_response.status_code == 401
