"""Tests unitarios para docker/django/entrypoint.py."""

import importlib.util
from pathlib import Path

import pytest


ENTRYPOINT_PATH = (
    Path(__file__).resolve().parents[1] / "docker" / "django" / "entrypoint.py"
)


def _load_entrypoint_module():
    spec = importlib.util.spec_from_file_location(
        "docker_django_entrypoint_test", ENTRYPOINT_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_run_command_fuerza_check_true(mocker):
    module = _load_entrypoint_module()
    mock_run = mocker.patch.object(module.subprocess, "run", return_value=object())

    module.run_command(["python", "manage.py", "check"], stage="check")

    mock_run.assert_called_once_with(["python", "manage.py", "check"], check=True)


def test_run_django_commands_incluye_makemigrations_en_dev_por_defecto(
    mocker, monkeypatch
):
    module = _load_entrypoint_module()
    mock_run_command = mocker.patch.object(module, "run_command")
    mock_run_server = mocker.patch.object(module, "run_server")
    monkeypatch.setenv("ENVIRONMENT", "dev")
    monkeypatch.delenv("RUN_MAKEMIGRATIONS_ON_START", raising=False)

    module.run_django_commands()

    stages = [call.kwargs["stage"] for call in mock_run_command.call_args_list]
    assert stages == [
        "makemigrations",
        "migrate auth",
        "migrate",
        "load_fixtures",
        "create_test_users",
        "create_groups",
    ]
    mock_run_server.assert_called_once_with()


def test_run_django_commands_omite_makemigrations_en_prd_por_defecto(
    mocker, monkeypatch
):
    module = _load_entrypoint_module()
    mock_run_command = mocker.patch.object(module, "run_command")
    mock_run_server = mocker.patch.object(module, "run_server")
    monkeypatch.setenv("ENVIRONMENT", "prd")
    monkeypatch.delenv("RUN_MAKEMIGRATIONS_ON_START", raising=False)

    module.run_django_commands()

    stages = [call.kwargs["stage"] for call in mock_run_command.call_args_list]
    assert "makemigrations" not in stages
    assert stages == [
        "migrate auth",
        "migrate",
        "load_fixtures",
        "create_test_users",
        "create_groups",
    ]
    mock_run_server.assert_called_once_with()


def test_run_django_commands_ignora_flag_legacy_run_makemigrations(
    mocker, monkeypatch
):
    module = _load_entrypoint_module()
    mock_run_command = mocker.patch.object(module, "run_command")
    mocker.patch.object(module, "run_server")
    monkeypatch.setenv("ENVIRONMENT", "prd")
    monkeypatch.delenv("RUN_MAKEMIGRATIONS_ON_START", raising=False)
    monkeypatch.setenv("RUN_MAKEMIGRATIONS", "true")

    module.run_django_commands()

    stages = [call.kwargs["stage"] for call in mock_run_command.call_args_list]
    assert "makemigrations" not in stages


@pytest.mark.parametrize("flag", ["true", "TRUE", "TrUe"])
def test_run_django_commands_respeta_flag_explicito_para_makemigrations(
    mocker, monkeypatch, flag
):
    module = _load_entrypoint_module()
    mock_run_command = mocker.patch.object(module, "run_command")
    mocker.patch.object(module, "run_server")
    monkeypatch.setenv("ENVIRONMENT", "prd")
    monkeypatch.setenv("RUN_MAKEMIGRATIONS_ON_START", flag)

    module.run_django_commands()

    stages = [call.kwargs["stage"] for call in mock_run_command.call_args_list]
    assert stages[0] == "makemigrations"
