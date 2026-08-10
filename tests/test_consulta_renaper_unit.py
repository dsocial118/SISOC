"""Tests unitarios para la integración compartida RENAPER."""

from types import SimpleNamespace

import pytest
import requests

import core.integrations.renaper as client_module
import core.services.renaper as module


class _ResponseMock:
    def __init__(self, payload=None, status_code=200):
        self.payload = payload
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


def test_api_client_uses_cached_token_without_request(mocker):
    client = client_module.APIClient()
    mocker.patch.object(client_module.cache, "get", return_value={"token": "token"})
    client.session = mocker.Mock()

    assert client.get_token() == "token"
    client.session.post.assert_not_called()


def test_api_client_logs_in_and_caches_token_with_configured_ttl(mocker, settings):
    settings.RENAPER_TOKEN_CACHE_TTL_SECONDS = 321
    session = mocker.Mock()
    session.post.return_value = _ResponseMock({"token": "token"})
    cache_set = mocker.patch.object(client_module.cache, "set")

    client = client_module.APIClient()
    client.session = session

    assert client.get_token() == "token"
    session.post.assert_called_once_with(
        client.login_url,
        json={"username": client.username, "password": client.password},
        timeout=settings.RENAPER_REQUEST_TIMEOUT_SECONDS,
    )
    cache_set.assert_called_once_with(
        client_module.TOKEN_CACHE_KEY,
        {"token": "token"},
        321,
    )


def test_api_client_clasifica_timeout_de_login_sin_loguear_credenciales(
    mocker, settings
):
    settings.RENAPER_API_USERNAME = "usuario-renaper"
    settings.RENAPER_API_PASSWORD = "secreto-renaper"
    session = mocker.Mock()
    session.post.side_effect = requests.Timeout()
    client = client_module.APIClient()
    client.session = session
    log_warning = mocker.patch.object(client_module.logger, "warning")

    with pytest.raises(
        client_module.RenaperServiceError, match="no respondio a tiempo"
    ) as exc:
        client.get_token()

    assert exc.value.error_type == "timeout"
    logged = str(log_warning.call_args)
    assert "usuario-renaper" not in logged
    assert "secreto-renaper" not in logged


@pytest.mark.parametrize(
    ("response", "error_type"),
    [
        (_HTTPErrorResponse({"detail": "forbidden"}, 403), "auth_error"),
        (_ResponseMock(ValueError("bad json")), "invalid_response"),
    ],
)
def test_api_client_clasifica_respuesta_invalida_o_error_de_login(
    mocker, response, error_type
):
    session = mocker.Mock()
    session.post.return_value = response
    client = client_module.APIClient()
    client.session = session

    with pytest.raises(client_module.RenaperServiceError) as exc:
        client.get_token()

    assert exc.value.error_type == error_type


def test_api_client_no_log_error_when_no_match(mocker):
    session = mocker.Mock()
    session.get.return_value = _ResponseMock({"isSuccess": False})

    client = client_module.APIClient()
    client.session = session
    mocker.patch.object(client, "get_token", return_value="token")
    log_warning = mocker.patch.object(client_module.logger, "warning")

    out = client.consultar_ciudadano("00000001", "M")

    assert out == {
        "success": False,
        "error": "No se encontro coincidencia.",
        "error_type": "no_match",
    }
    log_warning.assert_not_called()


def test_api_client_clasifica_timeout_y_no_loguea_datos_sensibles(mocker):
    session = mocker.Mock()
    session.get.side_effect = requests.Timeout()

    client = client_module.APIClient()
    client.session = session
    mocker.patch.object(client, "get_token", return_value="token")
    log_warning = mocker.patch.object(client_module.logger, "warning")

    out = client.consultar_ciudadano("00000001", "M")

    assert out == {
        "success": False,
        "error": "RENAPER no respondio a tiempo durante la consulta.",
        "error_type": "timeout",
    }
    logged = str(log_warning.call_args)
    assert "00000001" not in logged
    assert "token" not in logged


def test_api_client_clasifica_auth_error_without_raw_response(mocker):
    session = mocker.Mock()
    session.get.return_value = _HTTPErrorResponse({"detail": "unauthorized"}, 401)

    client = client_module.APIClient()
    client.session = session
    mocker.patch.object(client, "get_token", return_value="token")

    out = client.consultar_ciudadano("00000001", "M")

    assert out["success"] is False
    assert out["error_type"] == "auth_error"
    assert "raw_response" not in out


def test_api_client_clasifica_invalid_response_without_raw_response(mocker):
    session = mocker.Mock()
    session.get.return_value = _ResponseMock(ValueError("bad json"))

    client = client_module.APIClient()
    client.session = session
    mocker.patch.object(client, "get_token", return_value="token")

    out = client.consultar_ciudadano("00000001", "M")

    assert out["success"] is False
    assert out["error_type"] == "invalid_response"
    assert "raw_response" not in out


def test_consultar_datos_renaper_propagates_error_type_without_raw_response(mocker):
    client = mocker.Mock()
    client.consultar_ciudadano.return_value = {
        "success": False,
        "error": "upstream unavailable",
        "error_type": "remote_error",
    }
    mocker.patch("core.services.renaper.APIClient", return_value=client)

    out = module.consultar_datos_renaper("00000001", "M")

    assert out["success"] is False
    assert out["error_type"] == "remote_error"
    assert "raw_response" not in out


def test_consultar_datos_renaper_detecta_fallecido(mocker):
    client = mocker.Mock()
    client.consultar_ciudadano.return_value = {
        "success": True,
        "data": {"mensaf": "FALLECIDO"},
    }
    mocker.patch("core.services.renaper.APIClient", return_value=client)

    out = module.consultar_datos_renaper("00000001", "M")

    assert out["success"] is False
    assert out["error_type"] == "fallecido"
    assert out["fallecido"] is True


def test_consultar_datos_renaper_clasifica_payload_invalido(mocker):
    client = mocker.Mock()
    client.consultar_ciudadano.return_value = {
        "success": True,
        "data": "payload roto",
    }
    mocker.patch("core.services.renaper.APIClient", return_value=client)

    out = module.consultar_datos_renaper("00000001", "M")

    assert out["success"] is False
    assert out["error_type"] == "invalid_response"


def test_consultar_datos_renaper_ignora_placeholders_no_numericos(mocker):
    client = mocker.Mock()
    client.consultar_ciudadano.return_value = {
        "success": True,
        "data": {
            "cuil": "20000000019",
            "apellido": "Persona",
            "nombres": "Prueba",
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
    mocker.patch("core.services.renaper.APIClient", return_value=client)
    mocker.patch(
        "core.services.renaper.Sexo.objects.filter",
        return_value=SimpleNamespace(first=lambda: SimpleNamespace(pk=1)),
    )

    out = module.consultar_datos_renaper("00000001", "F")

    assert out["success"] is True
    assert out["data"]["tipo_documento"] == "DNI"
    assert out["data"]["codigo_postal"] is None
    assert out["data"]["altura"] is None
