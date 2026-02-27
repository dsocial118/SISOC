"""Reglas de mapeo de operadores de filtros avanzados a lookups ORM."""

from __future__ import annotations

from typing import Optional


def resolve_lookup(
    field_type: str, op: str, mapped_field: str
) -> tuple[Optional[str], bool]:
    """Resuelve lookup de Django y si debe negarse el ``Q`` resultante."""

    lookup = None
    negate = False

    if field_type == "text":
        if op == "eq":
            lookup = f"{mapped_field}__iexact"
        elif op == "ne":
            lookup = f"{mapped_field}__iexact"
            negate = True
        elif op == "contains":
            lookup = f"{mapped_field}__icontains"
        elif op == "ncontains":
            lookup = f"{mapped_field}__icontains"
            negate = True
    elif field_type == "choice":
        if op == "eq":
            lookup = f"{mapped_field}__iexact"
        elif op == "ne":
            lookup = f"{mapped_field}__iexact"
            negate = True
    elif field_type == "number":
        if op == "eq":
            lookup = f"{mapped_field}__exact"
        elif op == "ne":
            lookup = f"{mapped_field}__exact"
            negate = True
        elif op == "gt":
            lookup = f"{mapped_field}__gt"
        elif op == "lt":
            lookup = f"{mapped_field}__lt"
    elif field_type == "date":
        if op == "eq":
            lookup = f"{mapped_field}__exact"
        elif op == "ne":
            lookup = f"{mapped_field}__exact"
            negate = True
        elif op == "gt":
            lookup = f"{mapped_field}__gt"
        elif op == "lt":
            lookup = f"{mapped_field}__lt"
    elif field_type == "boolean":
        if op == "eq":
            lookup = f"{mapped_field}__exact"
        elif op == "ne":
            lookup = f"{mapped_field}__exact"
            negate = True

    return lookup, negate
