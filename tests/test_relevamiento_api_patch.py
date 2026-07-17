"""Tests del guard de entrada de PATCH /api/relevamiento."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient


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

    response = client.patch(
        "/api/relevamiento", {"sisoc_id": 999999}, format="json"
    )

    assert response.status_code == 404
