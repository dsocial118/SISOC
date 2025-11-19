"""Configuración para filtros combinables de equipos técnicos (duplas)."""

from typing import Any, Dict

# --- Backend -----------------------------------------------------------------

FIELD_MAP: Dict[str, str] = {
    "nombre": "nombre",
    "tecnico": "tecnico__first_name",
    "tecnico_apellido": "tecnico__last_name",
    "abogado": "abogado__first_name",
    "abogado_apellido": "abogado__last_name",
    "coordinador": "coordinador__first_name",
    "coordinador_apellido": "coordinador__last_name",
    "estado": "estado",
}

FIELD_TYPES: Dict[str, str] = {
    key: "text"
    for key in [
        "nombre",
        "tecnico",
        "tecnico_apellido",
        "abogado",
        "abogado_apellido",
        "coordinador",
        "coordinador_apellido",
        "estado",
    ]
}

TEXT_OPS = ["contains", "ncontains", "eq", "ne", "empty"]
NUM_OPS = ["eq", "ne", "gt", "lt", "empty"]

# --- Frontend ----------------------------------------------------------------

FILTER_FIELDS = [
    {"name": "nombre", "label": "Nombre", "type": "text"},
    {"name": "tecnico", "label": "Técnico (Nombre)", "type": "text"},
    {"name": "tecnico_apellido", "label": "Técnico (Apellido)", "type": "text"},
    {"name": "abogado", "label": "Abogado (Nombre)", "type": "text"},
    {"name": "abogado_apellido", "label": "Abogado (Apellido)", "type": "text"},
    {"name": "coordinador", "label": "Coordinador (Nombre)", "type": "text"},
    {"name": "coordinador_apellido", "label": "Coordinador (Apellido)", "type": "text"},
    {"name": "estado", "label": "Estado", "type": "text"},
]


def get_filters_ui_config() -> Dict[str, Any]:
    """Configuración serializable para la UI de filtros avanzados."""

    return {
        "fields": FILTER_FIELDS,
        "operators": {
            "text": list(TEXT_OPS),
            "number": list(NUM_OPS),
        },
        "defaultOperators": {
            "text": "contains",
            "number": "eq",
        },
    }


__all__ = [
    "FIELD_MAP",
    "FIELD_TYPES",
    "TEXT_OPS",
    "NUM_OPS",
    "FILTER_FIELDS",
    "get_filters_ui_config",
]
