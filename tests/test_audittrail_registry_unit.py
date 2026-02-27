"""Tests unitarios para constants/registry de audittrail."""

from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.core.exceptions import FieldDoesNotExist

from audittrail import constants
from audittrail import registry


def test_tracked_models_include_auth_user_with_sensitive_excludes():
    user_model = get_user_model()
    user_key = (user_model._meta.app_label, user_model._meta.model_name)

    allowlist = constants.get_tracked_model_allowlist()
    assert user_key in allowlist

    user_definition = allowlist[user_key]
    excluded_fields = user_definition.get_excluded_fields()
    assert "password" in excluded_fields

    try:
        user_model._meta.get_field("last_login")
    except FieldDoesNotExist:
        assert "last_login" not in excluded_fields
    else:
        assert "last_login" in excluded_fields


def test_register_tracked_models_uses_single_source_definitions(mocker):
    fake_model = mocker.MagicMock()
    fake_definition = SimpleNamespace(
        get_model=lambda: fake_model,
        get_excluded_fields=lambda: ["password"],
    )
    register_mock = mocker.Mock()

    mocker.patch(
        "audittrail.registry.get_tracked_model_definitions",
        return_value=[fake_definition],
    )
    mocker.patch.object(registry.auditlog, "_registry", {}, create=True)
    mocker.patch.object(registry.auditlog, "register", register_mock)

    registry.register_tracked_models()

    register_mock.assert_called_once_with(fake_model, exclude_fields=["password"])
