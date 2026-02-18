"""Tests for test users api permissions unit."""

from types import SimpleNamespace

from users.api_permissions import (
    IsPWAAuthenticatedToken,
    IsPWARepresentativeForComedor,
)


def _request(user):
    return SimpleNamespace(user=user)


def _view(kwargs=None):
    return SimpleNamespace(kwargs=kwargs or {})


def _user(is_authenticated=True):
    return SimpleNamespace(is_authenticated=is_authenticated)


def test_is_pwa_authenticated_token_rejects_missing_user():
    permission = IsPWAAuthenticatedToken()

    assert permission.has_permission(_request(None), _view()) is False


def test_is_pwa_authenticated_token_rejects_unauthenticated_user():
    permission = IsPWAAuthenticatedToken()

    assert (
        permission.has_permission(_request(_user(is_authenticated=False)), _view())
        is False
    )


def test_is_pwa_authenticated_token_delegates_to_service(mocker):
    permission = IsPWAAuthenticatedToken()
    user = _user()
    mock_is_pwa_user = mocker.patch(
        "users.api_permissions.is_pwa_user", return_value=True
    )

    assert permission.has_permission(_request(user), _view()) is True
    mock_is_pwa_user.assert_called_once_with(user)


def test_is_pwa_representative_rejects_missing_user():
    permission = IsPWARepresentativeForComedor()

    assert permission.has_permission(_request(None), _view({"pk": 1})) is False


def test_is_pwa_representative_rejects_unauthenticated_user():
    permission = IsPWARepresentativeForComedor()

    assert (
        permission.has_permission(
            _request(_user(is_authenticated=False)), _view({"pk": 1})
        )
        is False
    )


def test_is_pwa_representative_rejects_without_comedor_id():
    permission = IsPWARepresentativeForComedor()

    assert permission.has_permission(_request(_user()), _view()) is False


def test_is_pwa_representative_rejects_non_numeric_comedor_id():
    permission = IsPWARepresentativeForComedor()

    assert permission.has_permission(_request(_user()), _view({"pk": "abc"})) is False


def test_is_pwa_representative_uses_pk_and_service(mocker):
    permission = IsPWARepresentativeForComedor()
    user = _user()
    mock_is_representante = mocker.patch(
        "users.api_permissions.is_representante", return_value=True
    )

    assert permission.has_permission(_request(user), _view({"pk": "10"})) is True
    mock_is_representante.assert_called_once_with(user, 10)


def test_is_pwa_representative_uses_comedor_id_fallback(mocker):
    permission = IsPWARepresentativeForComedor()
    user = _user()
    mock_is_representante = mocker.patch(
        "users.api_permissions.is_representante", return_value=False
    )

    assert (
        permission.has_permission(_request(user), _view({"comedor_id": "15"})) is False
    )
    mock_is_representante.assert_called_once_with(user, 15)
