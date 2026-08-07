"""Helpers para ordenamiento persistente de listados paginados."""

from urllib.parse import urlencode


def apply_allowed_ordering(queryset, request_or_get, allowed, default):
    """Aplica un ordenamiento GET validado y agrega desempate estable."""

    params = getattr(request_or_get, "GET", request_or_get)
    requested = params.get("ordering", "") if hasattr(params, "get") else ""
    descending = requested.startswith("-")
    key = requested[1:] if descending else requested
    orm_field = allowed.get(key)

    if not orm_field:
        return queryset.order_by(*default)

    selected = f"-{orm_field}" if descending else orm_field
    return queryset.order_by(selected, "pk")


def build_ordering_header(request, *, key, title):
    """Construye metadata de encabezado conservando filtros GET existentes."""

    current = request.GET.get("ordering", "")
    is_ascending = current == key
    is_descending = current == f"-{key}"
    next_ordering = f"-{key}" if is_ascending else key

    params = request.GET.copy()
    params["ordering"] = next_ordering
    params.pop("page", None)

    return {
        "key": key,
        "title": title,
        "sort_url": f"?{urlencode(params, doseq=True)}",
        "sort_direction": (
            "asc" if is_ascending else "desc" if is_descending else None
        ),
    }
