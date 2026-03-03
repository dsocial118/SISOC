import logging
import os

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

logger = logging.getLogger(__name__)

_SENTRY_INITIALIZED = False
_SENTRY_ENVIRONMENT_IDENTIFIERS = {
    "prd": "sisoc-prd",
    "qa": "sisoc-qa",
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
        logger.warning("Valor inválido para float en configuración de Sentry: %s", value)
        return default


def initialize_sentry_sdk() -> None:
    global _SENTRY_INITIALIZED

    if _SENTRY_INITIALIZED:
        return

    sentry_enabled = _env_to_bool(os.getenv("SENTRY_ENABLED"), default=True)
    if not sentry_enabled:
        return

    environment = (os.getenv("ENVIRONMENT") or "dev").strip().lower()
    if environment not in _SENTRY_ENVIRONMENT_IDENTIFIERS:
        return

    sentry_environment = (
        os.getenv("SENTRY_ENVIRONMENT")
        or _SENTRY_ENVIRONMENT_IDENTIFIERS.get(environment)
        or environment
    )

    dsn = (os.getenv("SENTRY_DSN") or "").strip()
    if not dsn:
        return

    sentry_kwargs = {
        "dsn": dsn,
        "environment": sentry_environment,
        "send_default_pii": _env_to_bool(
            os.getenv("SENTRY_SEND_DEFAULT_PII"), default=False
        ),
        "traces_sample_rate": _env_to_float(
            os.getenv("SENTRY_TRACES_SAMPLE_RATE"), default=0.0
        ),
        "profiles_sample_rate": _env_to_float(
            os.getenv("SENTRY_PROFILES_SAMPLE_RATE"), default=0.0
        ),
        "integrations": [
            DjangoIntegration(),
            LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
        ],
    }

    release = (os.getenv("SENTRY_RELEASE") or "").strip()
    if release:
        sentry_kwargs["release"] = release

    sentry_sdk.init(**sentry_kwargs)
    _SENTRY_INITIALIZED = True
