import importlib.util
from pathlib import Path
from uuid import uuid4


SETTINGS_PATH = Path(__file__).resolve().parents[1] / "config" / "settings.py"


def _load_settings_module():
    module_name = f"config_settings_test_{uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, SETTINGS_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_settings_renaper_retry_uses_defaults_with_invalid_env(monkeypatch):
    monkeypatch.setenv("RENAPER_VALIDACION_MAX_RETRIES", "abc")
    monkeypatch.setenv("RENAPER_VALIDACION_BACKOFF_SECONDS", "")

    module = _load_settings_module()

    assert module.RENAPER_VALIDACION_MAX_RETRIES == 1
    assert module.RENAPER_VALIDACION_BACKOFF_SECONDS == 0.0


def test_settings_renaper_retry_parses_valid_env(monkeypatch):
    monkeypatch.setenv("RENAPER_VALIDACION_MAX_RETRIES", "3")
    monkeypatch.setenv("RENAPER_VALIDACION_BACKOFF_SECONDS", "0.25")

    module = _load_settings_module()

    assert module.RENAPER_VALIDACION_MAX_RETRIES == 3
    assert module.RENAPER_VALIDACION_BACKOFF_SECONDS == 0.25
