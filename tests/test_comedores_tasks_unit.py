"""Tests unitarios para comedores.tasks."""

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
