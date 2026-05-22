"""Tests unitarios para centrodefamilia.services.consulta_renaper.impl."""

from types import SimpleNamespace

import requests

import centrodefamilia.services.consulta_renaper as module
import VAT.services.consulta_renaper as vat_module


class _ResponseMock:
    def __init__(self, payload=None, text="", status_code=200):
        self.payload = payload
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        return None

    def json(self):
        if isinstance(self.payload, Exception):
            raise self.payload
        return self.payload


class _HTTPErrorResponse(_ResponseMock):
    def raise_for_status(self):
        raise requests.HTTPError(response=self)


def test_api_client_no_log_error_when_no_match(mocker):
    session = mocker.Mock()
    session.get.return_value = _ResponseMock({"isSuccess": False})

    client = module.APIClient()
    client.session = session
    mocker.patch.object(client, "get_token", return_value="token")
    log_error = mocker.patch(
        "centrodefamilia.services.consulta_renaper.impl.logger.error"
    )

    out = client.consultar_ciudadano("13163071", "M")

    assert out["success"] is False
    assert out["error_type"] == "no_match"
    log_error.assert_not_called()


def test_api_client_clasifica_timeout_en_consulta(mocker):
    session = mocker.Mock()
    session.get.side_effect = requests.Timeout()

    client = module.APIClient()
    client.session = session
    mocker.patch.object(client, "get_token", return_value="token")

    out = client.consultar_ciudadano("13163071", "M")

    assert out == {
        "success": False,
        "error": "RENAPER no respondio a tiempo durante la consulta.",
        "error_type": "timeout",
    }


def test_api_client_clasifica_auth_error_en_consulta(mocker):
    session = mocker.Mock()
    session.get.return_value = _HTTPErrorResponse(
        {"detail": "unauthorized"}, status_code=401
    )

    client = module.APIClient()
    client.session = session
    mocker.patch.object(client, "get_token", return_value="token")

    out = client.consultar_ciudadano("13163071", "M")

    assert out["success"] is False
    assert out["error_type"] == "auth_error"
    assert out["raw_response"] == {"detail": "unauthorized"}


def test_api_client_clasifica_invalid_response_en_consulta(mocker):
    session = mocker.Mock()
    session.get.return_value = _ResponseMock(
        ValueError("bad json"), text="<html>broken</html>"
    )

    client = module.APIClient()
    client.session = session
    mocker.patch.object(client, "get_token", return_value="token")

    out = client.consultar_ciudadano("13163071", "M")

    assert out["success"] is False
    assert out["error_type"] == "invalid_response"
    assert out["raw_response"] == "<html>broken</html>"


def test_consultar_datos_renaper_propagates_error_type(mocker):
    client = mocker.Mock()
    client.consultar_ciudadano.return_value = {
        "success": False,
        "error": "upstream unavailable",
        "error_type": "remote_error",
        "raw_response": {"detail": "boom"},
    }
    mocker.patch(
        "centrodefamilia.services.consulta_renaper.impl.APIClient", return_value=client
    )

    out = module.consultar_datos_renaper("13163071", "M")

    assert out["success"] is False
    assert out["error_type"] == "remote_error"
    assert out["raw_response"] == {"detail": "boom"}


def test_consultar_datos_renaper_detecta_fallecido(mocker):
    client = mocker.Mock()
    client.consultar_ciudadano.return_value = {
        "success": True,
        "data": {"mensaf": "FALLECIDO"},
    }
    mocker.patch(
        "centrodefamilia.services.consulta_renaper.impl.APIClient", return_value=client
    )

    out = module.consultar_datos_renaper("13163071", "M")

    assert out["success"] is False
    assert out["error_type"] == "fallecido"
    assert out["fallecido"] is True


def test_consultar_datos_renaper_clasifica_payload_invalido(mocker):
    client = mocker.Mock()
    client.consultar_ciudadano.return_value = {
        "success": True,
        "data": "payload roto",
    }
    mocker.patch(
        "centrodefamilia.services.consulta_renaper.impl.APIClient", return_value=client
    )

    out = module.consultar_datos_renaper("13163071", "M")

    assert out["success"] is False
    assert out["error_type"] == "invalid_response"


def test_consultar_datos_renaper_ignora_placeholders_no_numericos(mocker):
    client = mocker.Mock()
    client.consultar_ciudadano.return_value = {
        "success": True,
        "data": {
            "cuil": "20957903119",
            "apellido": "Perez",
            "nombres": "Ana",
            "fechaNacimiento": "2000-01-01",
            "provincia": "Buenos Aires",
            "municipio": "La Plata",
            "ciudad": "La Plata",
            "cpostal": "-",
            "calle": "Sin calle",
            "numero": "S/N",
            "pais": "Argentina",
        },
    }
    mocker.patch(
        "centrodefamilia.services.consulta_renaper.impl.APIClient", return_value=client
    )
    mocker.patch(
        "centrodefamilia.services.consulta_renaper.impl.Sexo.objects.filter",
        return_value=SimpleNamespace(first=lambda: SimpleNamespace(pk=1)),
    )
    log_error = mocker.patch(
        "centrodefamilia.services.consulta_renaper.impl.logger.error"
    )

    out = module.consultar_datos_renaper("95790311", "F")

    assert out["success"] is True
    assert out["data"]["codigo_postal"] is None
    assert out["data"]["altura"] is None
    log_error.assert_not_called()


def test_vat_consultar_datos_renaper_ignora_placeholders_no_numericos(mocker):
    client = mocker.Mock()
    client.consultar_ciudadano.return_value = {
        "success": True,
        "data": {
            "cuil": "20957903119",
            "apellido": "Perez",
            "nombres": "Ana",
            "fechaNacimiento": "2000-01-01",
            "provincia": "Buenos Aires",
            "municipio": "La Plata",
            "ciudad": "La Plata",
            "cpostal": "-",
            "calle": "Sin calle",
            "numero": "S/N",
            "pais": "Argentina",
        },
    }
    mocker.patch("VAT.services.consulta_renaper.impl.APIClient", return_value=client)
    mocker.patch(
        "VAT.services.consulta_renaper.impl.Sexo.objects.filter",
        return_value=SimpleNamespace(first=lambda: SimpleNamespace(pk=1)),
    )
    log_error = mocker.patch("VAT.services.consulta_renaper.impl.logger.error")

    out = vat_module.consultar_datos_renaper("95790311", "F")

    assert out["success"] is True
    assert out["data"]["codigo_postal"] is None
    assert out["data"]["altura"] is None
    log_error.assert_not_called()
