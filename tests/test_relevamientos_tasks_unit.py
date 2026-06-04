"""Tests unitarios para relevamientos.tasks."""

import pytest

from relevamientos import tasks as module


def test_run_async_threads_disabled_by_pytest_env(monkeypatch):
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "tests::algo")

    assert module._run_async_threads() is False


def test_run_async_threads_disabled_by_flag(monkeypatch):
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.setenv("DISABLE_ASYNC_THREADS", "true")

    assert module._run_async_threads() is False


def test_async_send_start_runs_inline_in_tests(mocker, monkeypatch):
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "tests::algo")
    mocker.patch("relevamientos.tasks.settings.GESTIONAR_INTEGRATION_ENABLED", True)
    thread = module.AsyncSendRelevamientoToGestionar(relevamiento_id=1, payload={})
    mock_run = mocker.patch.object(thread, "run")
    mock_submit = mocker.patch.object(module._EXECUTOR, "submit")

    result = thread.start()

    assert result is None
    mock_run.assert_called_once_with()
    mock_submit.assert_not_called()


def test_async_remove_start_uses_executor_fuera_de_tests(mocker, monkeypatch):
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.delenv("DISABLE_ASYNC_THREADS", raising=False)
    mocker.patch("relevamientos.tasks.settings.GESTIONAR_INTEGRATION_ENABLED", True)
    thread = module.AsyncRemoveRelevamientoToGestionar(relevamiento_id=1)
    mock_run = mocker.patch.object(thread, "run")
    mock_submit = mocker.patch.object(module._EXECUTOR, "submit")

    result = thread.start()

    assert result is None
    mock_submit.assert_called_once_with(mock_run)
    mock_run.assert_not_called()


def test_async_send_start_omits_when_integration_disabled(mocker, monkeypatch):
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.delenv("DISABLE_ASYNC_THREADS", raising=False)
    mocker.patch("relevamientos.tasks.settings.GESTIONAR_INTEGRATION_ENABLED", False)
    thread = module.AsyncSendRelevamientoToGestionar(relevamiento_id=1, payload={})
    mock_run = mocker.patch.object(thread, "run")
    mock_submit = mocker.patch.object(module._EXECUTOR, "submit")

    result = thread.start()

    assert result is None
    mock_submit.assert_not_called()
    mock_run.assert_not_called()


@pytest.mark.django_db
def test_async_send_relevamiento_marca_sincronizado_con_filas(mocker, settings):
    from comedores.models import Comedor
    from relevamientos.models import Relevamiento

    comedor = Comedor.objects.create(nombre="Comedor Sync Relevamiento")
    # Se crea con la integracion apagada (default en tests) para que el signal
    # no dispare un POST real durante el alta.
    relevamiento = Relevamiento.objects.create(comedor=comedor, estado="En Proceso")

    settings.GESTIONAR_INTEGRATION_ENABLED = True
    response = mocker.Mock()
    response.raise_for_status.return_value = None
    response.content = b'{"Rows": [{"docPDF": "https://gestionar.test/r.pdf"}]}'
    response.json.return_value = {"Rows": [{"docPDF": "https://gestionar.test/r.pdf"}]}
    mocker.patch("relevamientos.tasks.requests.post", return_value=response)

    module.AsyncSendRelevamientoToGestionar(
        relevamiento.id,
        module.build_relevamiento_payload(relevamiento),
    ).run()

    relevamiento.refresh_from_db()
    assert relevamiento.sincronizado_gestionar is True
    assert relevamiento.docPDF == "https://gestionar.test/r.pdf"


@pytest.mark.django_db
def test_async_send_relevamiento_no_marca_sincronizado_sin_filas(mocker, settings):
    from comedores.models import Comedor
    from relevamientos.models import Relevamiento

    comedor = Comedor.objects.create(nombre="Comedor Sync Relevamiento 2")
    relevamiento = Relevamiento.objects.create(comedor=comedor, estado="En Proceso")

    settings.GESTIONAR_INTEGRATION_ENABLED = True
    response = mocker.Mock()
    response.raise_for_status.return_value = None
    response.content = b'{"Rows": []}'
    response.json.return_value = {"Rows": []}
    mocker.patch("relevamientos.tasks.requests.post", return_value=response)

    module.AsyncSendRelevamientoToGestionar(
        relevamiento.id,
        module.build_relevamiento_payload(relevamiento),
    ).run()

    relevamiento.refresh_from_db()
    assert relevamiento.sincronizado_gestionar is False
