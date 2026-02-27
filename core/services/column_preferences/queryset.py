"""Helpers para optimización de queryset y exportes según columnas activas."""

from __future__ import annotations

from typing import Iterable

from .definitions import ColumnDefinition


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
