"""Contratos de parsing de configuración sensible."""

from config import settings as project_settings


def test_safe_positive_float_env_usa_default_ante_timeout_no_positivo(monkeypatch):
    monkeypatch.setenv("RENAPER_TEST_TIMEOUT", "0")

    assert (
        project_settings._safe_positive_float_env("RENAPER_TEST_TIMEOUT", 10.0) == 10.0
    )
