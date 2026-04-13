import importlib
import logging
import os

import sentry_sdk  # pylint: disable=import-error
from django.conf import settings
from sentry_sdk.utils import BadDsn, Dsn  # pylint: disable=import-error

logger = logging.getLogger(__name__)

_SENTRY_INITIALIZED = False
_SENTRY_ENVIRONMENT_IDENTIFIERS = {
    "prd": "sisoc-prd",
    "qa": "sisoc-qa",
    "hml": "sisoc-hml",
}
_SENTRY_LOG_LEVELS = {
    "critical": logging.CRITICAL,
    "error": logging.ERROR,
    "warning": logging.WARNING,
    "info": logging.INFO,
    "debug": logging.DEBUG,
}


def _env_to_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_to_float(value: str, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        logger.warning(
            "Valor invalido para float en configuracion de Sentry: %s", value
        )
        return default


def _env_to_log_level(value: str, default: int = logging.ERROR) -> int:
    if value is None:
        return default

    normalized = value.strip().lower()
    log_level = _SENTRY_LOG_LEVELS.get(normalized)
    if log_level is None:
        logger.warning(
            "Valor invalido para nivel de log en configuracion de Sentry: %s", value
        )
        return default

    return log_level


def _runtime_environment() -> str:
    return (os.getenv("ENVIRONMENT") or "dev").strip().lower()


def _is_sentry_available_for_environment(environment: str) -> bool:
    return environment in _SENTRY_ENVIRONMENT_IDENTIFIERS


def _resolve_sentry_environment(environment: str) -> str:
    # Resolver siempre a partir de ENVIRONMENT, sin permitir override por variable extra
    return _SENTRY_ENVIRONMENT_IDENTIFIERS.get(environment) or environment


def _build_sentry_integrations(sentry_log_event_level: int) -> list:
    django_integration = importlib.import_module(
        "sentry_sdk.integrations.django"
    ).DjangoIntegration
    logging_integration = importlib.import_module(
        "sentry_sdk.integrations.logging"
    ).LoggingIntegration
    return [
        django_integration(),
        logging_integration(level=logging.INFO, event_level=sentry_log_event_level),
    ]


def get_sentry_frontend_config() -> dict:
    environment = _runtime_environment()
    dsn = (getattr(settings, "SENTRY_DSN", "") or "").strip()
    if dsn:
        try:
            Dsn(dsn)
        except (BadDsn, ValueError):
            dsn = ""

    sentry_enabled = _env_to_bool(os.getenv("SENTRY_ENABLED"), default=True)
    replay_enabled = bool(getattr(settings, "SENTRY_REPLAY_ENABLED", False))

    enabled = (
        sentry_enabled
        and _is_sentry_available_for_environment(environment)
        and bool(dsn)
    )
    sentry_environment = _resolve_sentry_environment(environment)

    return {
        "enabled": enabled,
        "dsn": dsn,
        "environment": sentry_environment,
        "release": (os.getenv("SENTRY_RELEASE") or "").strip(),
        "send_default_pii": _env_to_bool(
            os.getenv("SENTRY_SEND_DEFAULT_PII"), default=False
        ),
        "sample_rate": _env_to_float(
            getattr(settings, "SENTRY_ERROR_SAMPLE_RATE", 1.0), default=1.0
        ),
        "replay_enabled": replay_enabled,
        "traces_sample_rate": _env_to_float(
            getattr(settings, "SENTRY_TRACES_SAMPLE_RATE", 0.0), default=0.0
        ),
        "replays_session_sample_rate": _env_to_float(
            getattr(settings, "SENTRY_REPLAYS_SESSION_SAMPLE_RATE", 0.0), default=0.0
        ),
        "replays_on_error_sample_rate": _env_to_float(
            getattr(settings, "SENTRY_REPLAYS_ON_ERROR_SAMPLE_RATE", 1.0), default=1.0
        ),
    }


def initialize_sentry_sdk() -> None:
    if _SENTRY_INITIALIZED:
        return

    sentry_enabled = _env_to_bool(os.getenv("SENTRY_ENABLED"), default=True)
    if not sentry_enabled:
        return

    environment = _runtime_environment()
    if not _is_sentry_available_for_environment(environment):
        return

    sentry_environment = _resolve_sentry_environment(environment)

    dsn = (getattr(settings, "SENTRY_DSN", "") or "").strip()
    if not dsn:
        return
    try:
        Dsn(dsn)
    except (BadDsn, ValueError) as exc:
        logger.warning(
            "SENTRY_DSN invalido. Se omite inicializacion de Sentry. Motivo: %s",
            exc,
        )
        return

    sentry_log_event_level = _env_to_log_level(
        getattr(settings, "SENTRY_LOG_EVENT_LEVEL", "WARNING"), default=logging.WARNING
    )
    sentry_kwargs = {
        "dsn": dsn,
        "environment": sentry_environment,
        "send_default_pii": _env_to_bool(
            os.getenv("SENTRY_SEND_DEFAULT_PII"), default=False
        ),
        "sample_rate": _env_to_float(
            getattr(settings, "SENTRY_ERROR_SAMPLE_RATE", 1.0), default=1.0
        ),
        "traces_sample_rate": _env_to_float(
            getattr(settings, "SENTRY_TRACES_SAMPLE_RATE", 0.0), default=0.0
        ),
        "profiles_sample_rate": _env_to_float(
            getattr(settings, "SENTRY_PROFILES_SAMPLE_RATE", 0.0), default=0.0
        ),
        "integrations": _build_sentry_integrations(sentry_log_event_level),
    }

    release = (os.getenv("SENTRY_RELEASE") or "").strip()
    if release:
        sentry_kwargs["release"] = release

    sentry_sdk.init(**sentry_kwargs)
    globals()["_SENTRY_INITIALIZED"] = True
