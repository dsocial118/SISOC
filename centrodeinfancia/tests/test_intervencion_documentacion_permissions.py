import json
from types import SimpleNamespace

import pytest
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory
from django.urls import reverse

from centrodeinfancia.urls import urlpatterns


class _GroupsResult:
    def __init__(self, allowed):
        self._allowed = allowed

    def exists(self):
        return self._allowed


class _GroupsManager:
    def __init__(self, allowed):
        self._allowed = allowed

    def filter(self, **_kwargs):
        return _GroupsResult(self._allowed)


class _UserStub:
    def __init__(self, in_group=False, authenticated=True, is_superuser=False):
        self.is_authenticated = authenticated
        self.is_superuser = is_superuser
        self.groups = _GroupsManager(in_group)


def _callback(name):
    for pattern in urlpatterns:
        if pattern.name == name:
            return pattern.callback
    raise AssertionError(f"No se encontró la ruta {name}")


def test_subir_documentacion_requires_group():
    request = RequestFactory().post(
        "/centrodeinfancia/intervencion/1/documentacion/subir/", data={}
    )
    request.user = _UserStub(in_group=False)

    with pytest.raises(PermissionDenied):
        _callback("centrodeinfancia_subir_archivo_intervencion")(
            request, intervencion_id=1
        )


def test_subir_documentacion_requires_post_even_with_group():
    request = RequestFactory().get(
        "/centrodeinfancia/intervencion/1/documentacion/subir/"
    )
    request.user = _UserStub(in_group=True)

    response = _callback("centrodeinfancia_subir_archivo_intervencion")(
        request, intervencion_id=1
    )

    assert response.status_code == 405


def test_subir_documentacion_post_without_file_returns_json_error(mocker):
    request = RequestFactory().post(
        "/centrodeinfancia/intervencion/1/documentacion/subir/", data={}
    )
    request.user = _UserStub(in_group=True)
    mocker.patch("centrodeinfancia.views.get_object_or_404", return_value=object())

    response = _callback("centrodeinfancia_subir_archivo_intervencion")(
        request, intervencion_id=1
    )

    assert response.status_code == 200
    assert json.loads(response.content) == {
        "success": False,
        "message": "No se proporcionó un archivo.",
    }


def test_eliminar_documentacion_requires_group():
    request = RequestFactory().post(
        "/centrodeinfancia/intervencion/1/documentacion/eliminar/", data={}
    )
    request.user = _UserStub(in_group=False)

    with pytest.raises(PermissionDenied):
        _callback("centrodeinfancia_eliminar_archivo_intervencion")(
            request, intervencion_id=1
        )


def test_eliminar_documentacion_requires_post_even_with_group():
    request = RequestFactory().get(
        "/centrodeinfancia/intervencion/1/documentacion/eliminar/"
    )
    request.user = _UserStub(in_group=True)

    response = _callback("centrodeinfancia_eliminar_archivo_intervencion")(
        request, intervencion_id=1
    )

    assert response.status_code == 405


def test_eliminar_documentacion_post_without_file_redirects(mocker):
    request = RequestFactory().post(
        "/centrodeinfancia/intervencion/1/documentacion/eliminar/", data={}
    )
    request.user = _UserStub(in_group=True)
    mocker.patch("centrodeinfancia.views.messages.error")
    mocker.patch(
        "centrodeinfancia.views.get_object_or_404",
        return_value=SimpleNamespace(
            documentacion=None,
            tiene_documentacion=False,
            centro_id=99,
        ),
    )

    response = _callback("centrodeinfancia_eliminar_archivo_intervencion")(
        request, intervencion_id=1
    )

    assert response.status_code == 302
    assert response.url == reverse("centrodeinfancia_detalle", kwargs={"pk": 99})
