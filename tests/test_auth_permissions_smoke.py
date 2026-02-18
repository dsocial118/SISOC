"""Tests for test auth permissions smoke."""

import pytest
from django.contrib.auth import SESSION_KEY

pytestmark = [pytest.mark.smoke, pytest.mark.django_db]

LOGIN_PATH = "/"
API_CATEGORIAS_PATH = "/api/centrodefamilia/categorias/"


def test_login_success(client, user):
    response = client.post(
        LOGIN_PATH,
        data={"username": user.username, "password": "testpass"},
    )

    assert response.status_code in {302, 303}
    assert SESSION_KEY in client.session


def test_login_invalid(client, user):
    response = client.post(
        LOGIN_PATH,
        data={"username": user.username, "password": "wrong-pass"},
    )

    assert response.status_code in {200, 400, 401}
    assert SESSION_KEY not in client.session


def test_api_requires_key(client, api_client):
    anon_response = client.get(API_CATEGORIAS_PATH)
    assert anon_response.status_code in {401, 403}

    auth_response = api_client.get(API_CATEGORIAS_PATH)
    assert auth_response.status_code == 200
