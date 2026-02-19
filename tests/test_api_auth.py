"""Tests for test api auth."""

import types

import pytest
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIRequestFactory
from rest_framework_api_key.models import APIKey

from core.api_auth import HasAPIKeyOrToken


@pytest.fixture(name="api_key_validator")
def _api_key_validator(monkeypatch):
    calls = {}

    def _fake_is_valid(key: str) -> bool:
        calls["last_key"] = key
        return key == "valid-api-key"

    monkeypatch.setattr(APIKey.objects, "is_valid", _fake_is_valid)
    return calls


def test_has_permission_accepts_authorization_api_key_prefix(api_key_validator):
    request = APIRequestFactory().get(
        "/relevamientos", HTTP_AUTHORIZATION="Api-Key valid-api-key"
    )
    request.user = AnonymousUser()

    assert HasAPIKeyOrToken().has_permission(request, None)
    assert api_key_validator["last_key"] == "valid-api-key"


def test_has_permission_accepts_legacy_api_key_header(api_key_validator):
    request = APIRequestFactory().get("/relevamientos", HTTP_API_KEY="valid-api-key")
    request.user = AnonymousUser()

    assert HasAPIKeyOrToken().has_permission(request, None)
    assert api_key_validator["last_key"] == "valid-api-key"


def test_has_permission_rejects_invalid_api_key(api_key_validator):
    request = APIRequestFactory().get(
        "/relevamientos", HTTP_AUTHORIZATION="Api-Key invalid"
    )
    request.user = AnonymousUser()

    assert HasAPIKeyOrToken().has_permission(request, None) is False
    assert api_key_validator["last_key"] == "invalid"


def test_has_permission_accepts_authenticated_user_without_api_key():
    request = APIRequestFactory().get("/relevamientos")
    request.user = types.SimpleNamespace(is_authenticated=True)

    assert HasAPIKeyOrToken().has_permission(request, None)
