"""Gestion de preferencias de columnas por listado."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Optional

from django.urls import reverse

from core.models import PreferenciaColumnas


@dataclass(frozen=True)
class ColumnDefinition:
    key: str
    title: str
    field: Mapping[str, Any]
    header: Optional[Mapping[str, Any]] = None
    default: bool = True
    required: bool = False
    export_field: Optional[str] = None
    export_title: Optional[str] = None
    sort_field: Optional[str] = None
    select_related: tuple[str, ...] = ()
    prefetch_related: tuple[str, ...] = ()
    only_fields: tuple[str, ...] = ()

    def build_header(self) -> dict[str, Any]:
        header = {"title": self.title}
        if self.header:
            header.update(self.header)
        return header

    def build_field(self) -> dict[str, Any]:
        field = dict(self.field)
        field.setdefault("name", self.key)
        return field


@dataclass
class ColumnResolution:
    active_keys: list[str]
    default_keys: list[str]
    available_keys: list[str]


_CACHE_ATTR = "_column_preferences_cache"


def _cache_for_request(request) -> dict[str, ColumnResolution]:
    if request is None:
        return {}
    cache = getattr(request, _CACHE_ATTR, None)
    if cache is None:
        cache = {}
        setattr(request, _CACHE_ATTR, cache)
    return cache


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


def _build_column_config(
    list_key: str,
    available: Iterable[Mapping[str, Any]],
    resolution: ColumnResolution,
) -> dict[str, Any]:
    safe_id = _sanitize_id(list_key)
    return {
        "list_key": list_key,
        "endpoint": reverse("column_preferences"),
        "modal_id": f"column-config-modal-{safe_id}",
        "script_id": f"column-config-data-{safe_id}",
        "available": list(available),
        "active": list(resolution.active_keys),
        "defaults": list(resolution.default_keys),
    }


def build_columns_context_from_fields(
    request,
    list_key: str,
    table_headers: Iterable[Any],
    table_fields: Iterable[Mapping[str, Any]],
    default_keys: Optional[list[str]] = None,
    required_keys: Optional[Iterable[str]] = None,
    headers_key: str = "table_headers",
    fields_key: str = "table_fields",
) -> dict[str, Any]:
    headers_list = list(table_headers)
    fields_list = list(table_fields)

    field_keys_raw = [
        str(field.get("key") or field.get("name") or "").strip()
        for field in fields_list
    ]
    field_keys = _ensure_unique_keys(field_keys_raw)
    header_by_key: dict[str, Any] = {}
    field_by_key: dict[str, Mapping[str, Any]] = {}
    available = []

    for idx, key in enumerate(field_keys):
        header = headers_list[idx] if idx < len(headers_list) else {"title": key}
        if isinstance(header, dict):
            title = header.get("title") or key
            header_by_key[key] = header
        else:
            title = str(header)
            header_by_key[key] = {"title": title}
        field_by_key[key] = fields_list[idx]
        available.append(
            {
                "key": key,
                "title": title,
                "active": True,
                "required": False,
                "default": True,
            }
        )

    resolution = _resolve_column_state_from_keys(
        request,
        list_key,
        [col["key"] for col in available],
        default_keys=default_keys,
        required_keys=required_keys,
    )

    active_headers = [
        header_by_key[key] for key in resolution.active_keys if key in header_by_key
    ]
    active_fields = [
        field_by_key[key] for key in resolution.active_keys if key in field_by_key
    ]

    for col in available:
        col_key = col["key"]
        col["active"] = col_key in resolution.active_keys
        col["default"] = col_key in resolution.default_keys

    column_config = _build_column_config(list_key, available, resolution)

    return {
        headers_key: active_headers,
        fields_key: active_fields,
        "column_config": column_config,
        "column_active_keys": list(resolution.active_keys),
        "column_default_keys": list(resolution.default_keys),
    }


def build_columns_context_for_custom_cells(
    request,
    list_key: str,
    table_headers: Iterable[Any],
    items: Iterable[Any],
    default_keys: Optional[list[str]] = None,
    required_keys: Optional[Iterable[str]] = None,
    headers_key: str = "table_headers",
    items_key: str = "table_items",
) -> dict[str, Any]:
    headers_list = []
    raw_keys = []

    for header in table_headers:
        if isinstance(header, dict):
            title = header.get("title") or header.get("label") or ""
            key = str(header.get("key") or header.get("sort_key") or title).strip()
            headers_list.append(header)
            raw_keys.append(key or title)
        else:
            title = str(header)
            headers_list.append({"title": title})
            raw_keys.append(title)

    available_keys = _ensure_unique_keys(raw_keys)
    header_by_key = {key: headers_list[idx] for idx, key in enumerate(available_keys)}
    index_by_key = {key: idx for idx, key in enumerate(available_keys)}

    resolution = _resolve_column_state_from_keys(
        request,
        list_key,
        available_keys,
        default_keys=default_keys,
        required_keys=required_keys,
    )

    active_headers = [
        header_by_key[key] for key in resolution.active_keys if key in header_by_key
    ]
    updated_items = []
    for item in list(items):
        if isinstance(item, dict) and isinstance(item.get("cells"), list):
            original_cells = item.get("cells", [])
            new_cells = []
            for key in resolution.active_keys:
                idx = index_by_key.get(key)
                if idx is None or idx >= len(original_cells):
                    continue
                new_cells.append(original_cells[idx])
            item = dict(item)
            item["cells"] = new_cells
        updated_items.append(item)

    available = []
    for key, header in header_by_key.items():
        title = header.get("title") if isinstance(header, dict) else str(header)
        available.append(
            {
                "key": key,
                "title": title,
                "active": key in resolution.active_keys,
                "required": False,
                "default": key in resolution.default_keys,
            }
        )

    column_config = _build_column_config(list_key, available, resolution)

    return {
        headers_key: active_headers,
        items_key: updated_items,
        "column_config": column_config,
        "column_active_keys": list(resolution.active_keys),
        "column_default_keys": list(resolution.default_keys),
    }


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


def build_columns_context(
    request,
    list_key: str,
    catalog: Iterable[ColumnDefinition],
    default_keys: Optional[list[str]] = None,
    headers_key: str = "table_headers",
    fields_key: str = "table_fields",
) -> dict[str, Any]:
    catalog_list = list(catalog)
    catalog_map = {col.key: col for col in catalog_list}

    resolution = resolve_column_state(request, list_key, catalog_list, default_keys)

    headers = [catalog_map[key].build_header() for key in resolution.active_keys]
    fields = [catalog_map[key].build_field() for key in resolution.active_keys]

    available = []
    for col in catalog_list:
        available.append(
            {
                "key": col.key,
                "title": col.title,
                "active": col.key in resolution.active_keys,
                "required": col.required,
                "default": col.key in resolution.default_keys,
            }
        )

    column_config = _build_column_config(list_key, available, resolution)

    return {
        headers_key: headers,
        fields_key: fields,
        "column_config": column_config,
        "column_active_keys": list(resolution.active_keys),
        "column_default_keys": list(resolution.default_keys),
    }


def apply_queryset_column_hints(
    queryset,
    catalog: Iterable[ColumnDefinition],
    active_keys: Iterable[str],
):
    catalog_map = {col.key: col for col in catalog}
    select_related = set()
    prefetch_related = set()
    only_fields = set()

    for key in active_keys:
        col = catalog_map.get(key)
        if not col:
            continue
        select_related.update(col.select_related)
        prefetch_related.update(col.prefetch_related)
        only_fields.update(col.only_fields)

    if select_related:
        queryset = queryset.select_related(*sorted(select_related))
    if prefetch_related:
        queryset = queryset.prefetch_related(*sorted(prefetch_related))
    if only_fields:
        queryset = queryset.only(*sorted(only_fields))

    return queryset


def build_export_columns(
    catalog: Iterable[ColumnDefinition],
    active_keys: Iterable[str],
) -> list[tuple[str, str]]:
    catalog_map = {col.key: col for col in catalog}
    columns = []
    for key in active_keys:
        col = catalog_map.get(key)
        if not col:
            continue
        export_title = col.export_title or col.title
        export_field = col.export_field or col.field.get("name")
        if export_field:
            columns.append((export_title, export_field))
    return columns


def build_export_sort_map(catalog: Iterable[ColumnDefinition]) -> dict[str, str]:
    sort_map: dict[str, str] = {}
    for col in catalog:
        if col.sort_field:
            sort_map[col.key] = col.sort_field
    return sort_map


__all__ = [
    "ColumnDefinition",
    "ColumnResolution",
    "apply_queryset_column_hints",
    "build_columns_context",
    "build_columns_context_for_custom_cells",
    "build_columns_context_from_fields",
    "build_export_columns",
    "build_export_sort_map",
    "resolve_column_state",
]
