"""Configuración de filtros combinables del listado de expedientes."""

from .impl import (
    CHOICE_OPS,
    DATE_OPS,
    FIELD_MAP,
    FIELD_TYPES,
    FILTER_FIELDS,
    NUM_OPS,
    TEXT_OPS,
    get_filters_ui_config,
)

__all__ = [
    "CHOICE_OPS",
    "DATE_OPS",
    "FIELD_MAP",
    "FIELD_TYPES",
    "FILTER_FIELDS",
    "NUM_OPS",
    "TEXT_OPS",
    "get_filters_ui_config",
]
