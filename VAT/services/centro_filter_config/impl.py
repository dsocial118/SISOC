"""Configuracion para filtros combinables de centros."""

from typing import Any, Dict

FIELD_MAP: Dict[str, str] = {
    "nombre": "nombre",
    "codigo": "codigo_cue",
}

FIELD_TYPES: Dict[str, str] = {
    "nombre": "text",
    "codigo": "text",
}

TEXT_OPS = ["contains", "ncontains", "eq", "ne", "empty"]
NUM_OPS = ["eq", "ne", "gt", "lt", "empty"]
BOOL_OPS = ["eq", "ne"]

FILTER_FIELDS = [
    {"name": "nombre", "label": "Nombre", "type": "text"},
    {"name": "codigo", "label": "Codigo", "type": "text"},
]


def get_filters_ui_config() -> Dict[str, Any]:
    return {
        "fields": FILTER_FIELDS,
        "operators": {
            "text": list(TEXT_OPS),
            "number": list(NUM_OPS),
            "boolean": list(BOOL_OPS),
        },
    }


__all__ = [
    "FIELD_MAP",
    "FIELD_TYPES",
    "TEXT_OPS",
    "NUM_OPS",
    "BOOL_OPS",
    "FILTER_FIELDS",
    "get_filters_ui_config",
]
