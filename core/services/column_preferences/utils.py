"""Helpers internos para preferencias de columnas."""

from __future__ import annotations

import re
from typing import Any, Iterable, Optional

from .definitions import ColumnDefinition


def _sanitize_id(value: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_-]+", "-", value or "")
    return safe.strip("-") or "list"


def _normalize_keys(value: Any) -> Optional[list[str]]:
    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip()
        if not value:
            return []
        return [part for part in value.split(",") if part]

    if isinstance(value, Iterable) and not isinstance(value, (dict, bytes)):
        return [str(item) for item in value if str(item)]

    return None


def _get_default_keys(
    catalog: Iterable[ColumnDefinition], default_keys: Optional[list[str]] = None
) -> list[str]:
    if default_keys:
        return list(default_keys)

    defaults = [col.key for col in catalog if col.default]
    if defaults:
        return defaults

    return [col.key for col in catalog]


def _ensure_unique_keys(keys: Iterable[str]) -> list[str]:
    unique = []
    seen: dict[str, int] = {}
    for key in keys:
        base = key or "col"
        count = seen.get(base, 0)
        if count:
            new_key = f"{base}_{count + 1}"
        else:
            new_key = base
        seen[base] = count + 1
        unique.append(new_key)
    return unique
