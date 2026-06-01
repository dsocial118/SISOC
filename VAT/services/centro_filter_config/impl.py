"""Configuracion para filtros combinables de centros."""

from typing import Any, Dict

FIELD_MAP: Dict[str, str] = {
    "nombre": "nombre",
    "codigo": "codigo_cue",
    "estado_carga": "estado_carga_completa",
}

FIELD_TYPES: Dict[str, str] = {
    "nombre": "text",
    "codigo": "text",
    "estado_carga": "boolean",
}

TEXT_OPS = ["contains", "ncontains", "eq", "ne", "empty"]
NUM_OPS = ["eq", "ne", "gt", "lt", "empty"]
BOOL_OPS = ["eq", "ne"]

FILTER_FIELDS = [
    {"name": "nombre", "label": "Nombre", "type": "text"},
    {"name": "codigo", "label": "Codigo", "type": "text"},
    {
        "name": "estado_carga",
        "label": "Estado de carga",
        "type": "boolean",
        "options": [
            {"value": True, "label": "COMPLETO"},
            {"value": False, "label": "INCOMPLETO"},
        ],
    },
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
