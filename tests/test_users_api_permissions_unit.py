"""Tests for test users api permissions unit."""

from types import SimpleNamespace

import pytest

from comedores.api_views import ComedorDetailViewSet
from pwa.api_views import (
    ActividadEspacioPWAViewSet,
    ColaboradorEspacioPWAViewSet,
    MensajeEspacioPWAViewSet,
    NominaEspacioPWAViewSet,
)

from users.api_permissions import (
    CanViewPwaUsuariosPermission,
    IsPWAAuthenticatedToken,
    IsPWARepresentativeForComedor,
    IsPWAWriteAllowed,
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


def test_is_pwa_representative_prioritizes_comedor_id_over_pk(mocker):
    permission = IsPWARepresentativeForComedor()
    user = _user()
    mock_is_representante = mocker.patch(
        "users.api_permissions.is_representante", return_value=True
    )

    assert (
        permission.has_permission(
            _request(user), _view({"comedor_id": "15", "pk": "999"})
        )
        is True
    )
    mock_is_representante.assert_called_once_with(user, 15)


def test_pwa_write_permission_rejects_read_only_coordinator(mocker):
    permission = IsPWAWriteAllowed()
    user = _user()
    mock_is_coordinador = mocker.patch(
        "users.api_permissions.is_coordinador_equipo_tecnico_pwa",
        return_value=True,
    )

    assert permission.has_permission(_request(user), _view()) is False
    mock_is_coordinador.assert_called_once_with(user)


def test_pwa_write_permission_allows_non_coordinator(mocker):
    permission = IsPWAWriteAllowed()
    user = _user()
    mocker.patch(
        "users.api_permissions.is_coordinador_equipo_tecnico_pwa",
        return_value=False,
    )

    assert permission.has_permission(_request(user), _view()) is True


def test_pwa_user_list_requires_representante_for_non_coordinator(mocker):
    permission = CanViewPwaUsuariosPermission()
    user = _user()
    mocker.patch(
        "users.api_permissions.is_coordinador_equipo_tecnico_pwa",
        return_value=False,
    )
    mocker.patch("users.api_permissions.is_representante", return_value=False)
    mocker.patch("users.api_permissions.user_has_permission_code", return_value=True)

    assert permission.has_permission(_request(user), _view({"pk": 15})) is False


def test_pwa_user_list_allows_coordinator_without_representante(mocker):
    permission = CanViewPwaUsuariosPermission()
    user = _user()
    mocker.patch(
        "users.api_permissions.is_coordinador_equipo_tecnico_pwa",
        return_value=True,
    )

    assert permission.has_permission(_request(user), _view({"pk": 15})) is True


@pytest.mark.parametrize(
    ("view_class", "action", "method"),
    [
        (ColaboradorEspacioPWAViewSet, "create", "POST"),
        (ActividadEspacioPWAViewSet, "create", "POST"),
        (NominaEspacioPWAViewSet, "create", "POST"),
        (MensajeEspacioPWAViewSet, "marcar_visto", "PATCH"),
    ],
)
def test_pwa_mutating_actions_include_read_only_veto(view_class, action, method):
    view = view_class()
    view.action = action
    view.request = SimpleNamespace(method=method)

    assert any(
        isinstance(permission, IsPWAWriteAllowed)
        for permission in view.get_permissions()
    )


@pytest.mark.parametrize(
    "action_name",
    [
        "upload_imagen",
        "eliminar_imagen",
        "subir_capacitacion",
        "eliminar_capacitacion",
        "editar_usuario_permisos",
        "desactivar_usuario",
        "adjuntar_documentacion_rendicion",
        "eliminar_documentacion_rendicion",
        "adjuntar_comprobante_rendicion",
        "presentar_rendicion",
        "eliminar_rendicion",
        "prestacion_alimentaria_conformidad",
    ],
)
def test_comedor_mutating_actions_include_read_only_veto(action_name):
    permission_classes = getattr(ComedorDetailViewSet, action_name).kwargs[
        "permission_classes"
    ]

    assert IsPWAWriteAllowed in permission_classes
