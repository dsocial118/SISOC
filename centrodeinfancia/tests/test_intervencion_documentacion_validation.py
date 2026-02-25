import json

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory

from centrodeinfancia.views import subir_archivo_intervencion_centrodeinfancia


class _UserStub:
    is_authenticated = True
    is_superuser = True
    id = 1


class _IntervencionStub:
    def __init__(self):
        self.documentacion = None
        self.tiene_documentacion = False
        self.saved_kwargs = None

    def save(self, **kwargs):
        self.saved_kwargs = kwargs


@pytest.mark.django_db
def test_subir_documentacion_rechaza_extension_no_permitida(mocker):
    request = RequestFactory().post(
        "/centrodeinfancia/intervencion/1/documentacion/subir/",
        data={"documentacion": SimpleUploadedFile("archivo.exe", b"123")},
    )
    request.user = _UserStub()
    mocker.patch(
        "centrodeinfancia.views.get_object_or_404",
        return_value=_IntervencionStub(),
    )

    response = subir_archivo_intervencion_centrodeinfancia(request, intervencion_id=1)

    assert response.status_code == 400
    payload = json.loads(response.content)
    assert payload["success"] is False
    assert "Formato de archivo no permitido" in payload["message"]


@pytest.mark.django_db
def test_subir_documentacion_rechaza_tamano_excedido(mocker):
    mocker.patch(
        "centrodeinfancia.views.DOCUMENTACION_INTERVENCION_MAX_SIZE_BYTES",
        10,
    )
    request = RequestFactory().post(
        "/centrodeinfancia/intervencion/1/documentacion/subir/",
        data={"documentacion": SimpleUploadedFile("archivo.pdf", b"12345678901")},
    )
    request.user = _UserStub()
    mocker.patch(
        "centrodeinfancia.views.get_object_or_404",
        return_value=_IntervencionStub(),
    )

    response = subir_archivo_intervencion_centrodeinfancia(request, intervencion_id=1)

    assert response.status_code == 400
    payload = json.loads(response.content)
    assert payload["success"] is False
    assert "tamaño máximo" in payload["message"]


@pytest.mark.django_db
def test_subir_documentacion_acepta_archivo_valido(mocker):
    intervencion = _IntervencionStub()
    request = RequestFactory().post(
        "/centrodeinfancia/intervencion/1/documentacion/subir/",
        data={"documentacion": SimpleUploadedFile("archivo.pdf", b"12345")},
    )
    request.user = _UserStub()
    mocker.patch("centrodeinfancia.views.get_object_or_404", return_value=intervencion)

    response = subir_archivo_intervencion_centrodeinfancia(request, intervencion_id=1)

    assert response.status_code == 200
    payload = json.loads(response.content)
    assert payload["success"] is True
    assert intervencion.tiene_documentacion is True
    assert intervencion.saved_kwargs == {"update_fields": ["documentacion", "tiene_documentacion"]}
