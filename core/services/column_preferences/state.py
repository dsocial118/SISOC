"""Resolución del estado activo/default de columnas por usuario y listado."""

from __future__ import annotations

from typing import Iterable, Optional

from core.models import PreferenciaColumnas

from .definitions import ColumnDefinition, ColumnResolution
from .utils import _get_default_keys

_CACHE_ATTR = "_column_preferences_cache"


def _cache_for_request(request) -> dict[str, ColumnResolution]:
    if request is None:
        return {}

    cache = getattr(request, _CACHE_ATTR, None)
    if cache is None:
        cache = {}
        setattr(request, _CACHE_ATTR, cache)
    return cache


def _resolve_column_state_from_keys(
    request,
    list_key: str,
    available_keys: Iterable[str],
    default_keys: Optional[list[str]] = None,
    required_keys: Optional[Iterable[str]] = None,
) -> ColumnResolution:
    cache = _cache_for_request(request)
    cache_key = f"{list_key}__keys"
    if cache_key in cache:
        return cache[cache_key]

    available = list(available_keys)
    defaults = list(default_keys) if default_keys else list(available)
    active_keys = list(defaults)

    if request is not None and getattr(request, "user", None) is not None:
        user = request.user
        if user.is_authenticated:
            pref = (
                PreferenciaColumnas.objects.filter(usuario=user, listado=list_key)
                .only("columnas")
                .first()
            )
            if pref and isinstance(pref.columnas, list):
                active_keys = [key for key in pref.columnas if key in available]

    required = list(required_keys) if required_keys else []
    for key in required:
        if key not in active_keys and key in available:
            active_keys.append(key)

    if not active_keys:
        active_keys = list(defaults)
        for key in required:
            if key not in active_keys and key in available:
                active_keys.append(key)

    resolution = ColumnResolution(
        active_keys=active_keys,
        default_keys=list(defaults),
        available_keys=available,
    )
    cache[cache_key] = resolution
    return resolution


def resolve_column_state(
    request,
    list_key: str,
    catalog: Iterable[ColumnDefinition],
    default_keys: Optional[list[str]] = None,
) -> ColumnResolution:
    cache = _cache_for_request(request)
    if list_key in cache:
        return cache[list_key]

    catalog_list = list(catalog)
    available_keys = [col.key for col in catalog_list]
    default_keys_resolved = _get_default_keys(catalog_list, default_keys)
    active_keys = list(default_keys_resolved)

    if request is not None and getattr(request, "user", None) is not None:
        user = request.user
        if user.is_authenticated:
            pref = (
                PreferenciaColumnas.objects.filter(usuario=user, listado=list_key)
                .only("columnas")
                .first()
            )
            if pref and isinstance(pref.columnas, list):
                active_keys = [key for key in pref.columnas if key in available_keys]

    required_keys = [col.key for col in catalog_list if col.required]
    for key in required_keys:
        if key not in active_keys:
            active_keys.append(key)

    if not active_keys:
        active_keys = list(default_keys_resolved)
        for key in required_keys:
            if key not in active_keys:
                active_keys.append(key)

    resolution = ColumnResolution(
        active_keys=active_keys,
        default_keys=list(default_keys_resolved),
        available_keys=available_keys,
    )
    cache[list_key] = resolution
    return resolution
