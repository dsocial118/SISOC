"""Utilidades para normalizar el payload de filtros avanzados."""

from __future__ import annotations

import json
from typing import Any, Mapping, MutableMapping, Optional


def extract_raw_filters(param_name: str, request_or_get: Any) -> Any:
    """Obtiene el valor del parámetro configurado desde distintas fuentes."""

    params: Optional[Mapping[str, Any]] = None

    # ``HttpRequest`` expone ``GET`` cuya lectura puede fallar en tests.
    if hasattr(request_or_get, "GET"):
        try:
            params = request_or_get.GET
        except Exception:  # pragma: no cover - protección adicional
            params = None

    if params is None:
        if isinstance(request_or_get, Mapping):
            params = request_or_get
        else:
            params = None

    if not params:
        return None

    try:
        return params.get(param_name)
    except Exception:  # pragma: no cover - compatibilidad con QueryDict
        return None


def load_payload(raw_filters: Any) -> Optional[dict[str, Any]]:
    """Decodifica el JSON enviado en el parámetro de filtros."""

    if isinstance(raw_filters, (bytes, bytearray)):
        raw_filters = raw_filters.decode()

    if isinstance(raw_filters, str):
        raw_filters = raw_filters.strip()
        if not raw_filters:
            return None
        try:
            parsed = json.loads(raw_filters)
        except (json.JSONDecodeError, TypeError):
            return None
    elif isinstance(raw_filters, MutableMapping):
        parsed = dict(raw_filters)
    elif isinstance(raw_filters, Mapping):
        parsed = dict(raw_filters)
    else:
        return None

    if not isinstance(parsed, dict):
        return None

    return parsed
