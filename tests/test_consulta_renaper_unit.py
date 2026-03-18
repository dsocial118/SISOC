"""Tests unitarios para centrodefamilia.services.consulta_renaper.impl."""

import centrodefamilia.services.consulta_renaper as module


class _ResponseMock:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


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
    assert out["error"] == "No se encontró coincidencia."
    log_error.assert_not_called()
