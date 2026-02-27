"""Builders de contexto para tablas con preferencias de columnas."""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional

from django.urls import reverse

from .definitions import ColumnDefinition, ColumnResolution
from .state import _resolve_column_state_from_keys, resolve_column_state
from .utils import _ensure_unique_keys, _sanitize_id


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
