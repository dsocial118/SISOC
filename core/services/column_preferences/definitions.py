"""Tipos de dominio para configuración de columnas."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional


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
