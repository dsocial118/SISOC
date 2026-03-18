"""Tests unitarios para comedores.tasks."""

import requests

from comedores import tasks as module


def test_async_send_comedor_start_omits_when_integration_disabled(mocker):
    mocker.patch("comedores.tasks.settings.GESTIONAR_INTEGRATION_ENABLED", False)
    thread = module.AsyncSendComedorToGestionar(payload={"Rows": []})
    mock_run = mocker.patch.object(thread, "run")
    mock_submit = mocker.patch.object(module._EXECUTOR, "submit")

    result = thread.start()

    assert result is None
    mock_submit.assert_not_called()
    mock_run.assert_not_called()


def test_async_remove_comedor_start_uses_executor_when_enabled(mocker):
    mocker.patch("comedores.tasks.settings.GESTIONAR_INTEGRATION_ENABLED", True)
    thread = module.AsyncRemoveComedorToGestionar(comedor_id=1)
    mock_run = mocker.patch.object(thread, "run")
    mock_submit = mocker.patch.object(module._EXECUTOR, "submit")

    result = thread.start()

    assert result is None
    mock_submit.assert_called_once_with(mock_run)
    mock_run.assert_not_called()


def test_build_comedor_payload_accepts_custom_action():
    comedor = type(
        "ComedorMock",
        (),
        {
            "id": 1,
            "nombre": "Comedor 1",
            "comienzo": None,
            "tipocomedor": None,
            "calle": "",
            "numero": "",
            "entre_calle_1": "",
            "entre_calle_2": "",
            "provincia": None,
            "municipio": None,
            "localidad": None,
            "partido": "",
            "barrio": "",
            "lote": "",
            "manzana": "",
            "piso": "",
            "longitud": "",
            "latitud": "",
            "programa": None,
            "organizacion": None,
            "departamento": "",
            "codigo_postal": "",
            "referente": None,
            "foto_legajo": "",
        },
    )()

    payload = module.build_comedor_payload(comedor, action="Update")

    assert payload["Action"] == "Update"


def test_async_send_comedor_run_retries_as_update_on_400(mocker):
    class _ResponseMock:
        def __init__(self, status_code, json_data=None):
            self.status_code = status_code
            self._json_data = json_data or {}

        def raise_for_status(self):
            if self.status_code >= 400:
                raise requests.HTTPError("boom", response=self)

        def json(self):
            return self._json_data

    mocker.patch("comedores.tasks.settings.GESTIONAR_INTEGRATION_ENABLED", True)
    mocker.patch("comedores.tasks.close_old_connections")
    post = mocker.patch(
        "comedores.tasks.requests.post",
        side_effect=[
            _ResponseMock(400),
            _ResponseMock(200, {"Rows": [{"ComedorID": 99}]}),
        ],
    )
    logger_exception = mocker.patch("comedores.tasks.logger.exception")

    thread = module.AsyncSendComedorToGestionar(
        payload={"Action": "Add", "Rows": [{"ComedorID": 99}]}
    )
    thread.run()

    assert post.call_count == 2
    assert post.call_args_list[0].kwargs["json"]["Action"] == "Add"
    assert post.call_args_list[1].kwargs["json"]["Action"] == "Update"
    logger_exception.assert_not_called()
