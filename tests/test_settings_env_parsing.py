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


def test_settings_email_backend_keeps_smtp_when_config_is_complete(monkeypatch):
    monkeypatch.setenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
    monkeypatch.setenv("EMAIL_HOST", "smtp.resend.com")
    monkeypatch.setenv("EMAIL_PORT", "587")
    monkeypatch.setenv("EMAIL_HOST_USER", "resend")
    monkeypatch.setenv("EMAIL_HOST_PASSWORD", "re_test_key")
    monkeypatch.setenv("EMAIL_USE_TLS", "true")
    monkeypatch.setenv("EMAIL_USE_SSL", "false")
    monkeypatch.setenv("DEFAULT_FROM_EMAIL", "SISOC <onboarding@resend.dev>")

    module = _load_settings_module()

    assert module.EMAIL_BACKEND == "django.core.mail.backends.smtp.EmailBackend"
    assert module.EMAIL_HOST == "smtp.resend.com"
    assert module.EMAIL_PORT == 587
    assert module.EMAIL_HOST_USER == "resend"
    assert module.DEFAULT_FROM_EMAIL == "SISOC <onboarding@resend.dev>"


def test_settings_email_backend_falls_back_to_console_when_smtp_is_incomplete(
    monkeypatch,
):
    monkeypatch.setenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
    monkeypatch.setenv("EMAIL_HOST", "smtp.resend.com")
    monkeypatch.setenv("EMAIL_PORT", "587")
    monkeypatch.setenv("EMAIL_HOST_USER", "resend")
    monkeypatch.delenv("EMAIL_HOST_PASSWORD", raising=False)

    module = _load_settings_module()

    assert module.EMAIL_BACKEND == "django.core.mail.backends.console.EmailBackend"


def test_settings_homologacion_usa_perfil_similar_a_produccion(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "homologacion")

    module = _load_settings_module()

    assert module.DEFAULT_SCHEME == "https"
    assert module.GESTIONAR_INTEGRATION_ENABLED is True
    assert module.DB_CONN_MAX_AGE == 60
    assert module.DB_CONN_HEALTH_CHECKS is True
    assert module.SECURE_SSL_REDIRECT is True
    assert module.SESSION_COOKIE_SECURE is True
    assert module.CSRF_COOKIE_SECURE is True
    assert module.SENTRY_REPLAY_ENABLED is True
    assert module.SENTRY_TRACES_SAMPLE_RATE == 1.0
    assert (
        module.STORAGES["staticfiles"]["BACKEND"]
        == "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
    )


def test_settings_homologacion_agrega_origen_local_para_csrf(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "homologacion")
    monkeypatch.setenv(
        "DJANGO_ALLOWED_HOSTS",
        "homologacion.sisoc.example.gov.ar,localhost,127.0.0.1",
    )
    monkeypatch.setenv("DOCKER_DJANGO_PORT_FORWARD", "8001")

    module = _load_settings_module()

    assert "https://homologacion.sisoc.example.gov.ar" in module.CSRF_TRUSTED_ORIGINS
    assert "http://localhost:8001" in module.CSRF_TRUSTED_ORIGINS
    assert "http://127.0.0.1:8001" in module.CSRF_TRUSTED_ORIGINS


def test_settings_qa_mantiene_runtime_no_productivo(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "qa")

    module = _load_settings_module()

    assert module.DEFAULT_SCHEME == "http"
    assert module.GESTIONAR_INTEGRATION_ENABLED is False
    assert module.SECURE_SSL_REDIRECT is False
    assert module.SENTRY_REPLAY_ENABLED is False
