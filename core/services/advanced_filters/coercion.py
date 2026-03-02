"""Casteos de valores para filtros avanzados."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Callable, Mapping


def coerce_value(
    *,
    field: str,
    value: Any,
    field_type: str,
    field_casts: Mapping[str, Callable[[Any], Any]],
) -> tuple[bool, Any]:
    """Intenta castear ``value`` según el tipo del campo."""

    if field in field_casts:
        try:
            return True, field_casts[field](value)
        except Exception:  # pragma: no cover - protección frente a errores
            return False, None

    if field_type == "number":
        try:
            return True, int(value)
        except (TypeError, ValueError):
            return False, None

    if field_type == "date":
        if isinstance(value, date) and not isinstance(value, datetime):
            return True, value

        if isinstance(value, datetime):
            return True, value.date()

        if isinstance(value, str):
            cleaned = value.strip()
            if not cleaned:
                return False, None

            if cleaned.endswith("Z"):
                cleaned = cleaned[:-1]

            try:
                return True, datetime.fromisoformat(cleaned).date()
            except ValueError:
                pass

            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
                try:
                    return True, datetime.strptime(cleaned, fmt).date()
                except ValueError:
                    continue

        return False, None

    if field_type == "boolean":
        truthy = {True, 1, "1", "true", "t", "yes", "y"}
        falsy = {False, 0, "0", "false", "f", "no", "n"}

        if isinstance(value, str):
            value = value.strip().lower()

        if value in truthy:
            return True, True

        if value in falsy:
            return True, False

        return False, None

    return True, value
