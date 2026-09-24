"""Filtros combinables para el listado de archivos importados.

Conserva lo que ya buscaba el listado (nombre de archivo y usuario) y suma los
datos del expediente y el resultado de la importacion que la tabla muestra.
"""

from copy import deepcopy
from typing import Any, Dict

from core.services.advanced_filters import AdvancedFilterEngine

FIELD_MAP: Dict[str, str] = {
    "archivo": "archivo",
    "usuario": "usuario__username",
    "numero_expediente_pago": "numero_expediente_pago",
    "mes_pago": "mes_pago",
    "ano_pago": "ano_pago",
    "count_errores": "count_errores",
    "count_exitos": "count_exitos",
    "importacion_completada": "importacion_completada",
    "fecha_subida": "fecha_subida",
}

FIELD_TYPES: Dict[str, str] = {
    "archivo": "text",
    "usuario": "text",
    "numero_expediente_pago": "text",
    "mes_pago": "text",
    "ano_pago": "text",
    "count_errores": "number",
    "count_exitos": "number",
    "importacion_completada": "boolean",
    "fecha_subida": "date",
}

TEXT_OPS = ["contains", "ncontains", "eq", "ne", "empty"]
NUM_OPS = ["eq", "ne", "gt", "lt", "empty"]
BOOL_OPS = ["eq", "ne"]
DATE_OPS = ["eq", "ne", "gt", "lt", "gte", "lte", "empty"]

FILTER_FIELDS = [
    {"name": "archivo", "label": "Archivo", "type": "text"},
    {"name": "usuario", "label": "Usuario", "type": "text"},
    {
        "name": "numero_expediente_pago",
        "label": "Número de expediente",
        "type": "text",
    },
    {"name": "mes_pago", "label": "Mes de pago", "type": "text"},
    {"name": "ano_pago", "label": "Año de pago", "type": "text"},
    {"name": "count_errores", "label": "Cantidad de errores", "type": "number"},
    {"name": "count_exitos", "label": "Cantidad de éxitos", "type": "number"},
    {
        "name": "importacion_completada",
        "label": "Importación completada?",
        "type": "boolean",
        "choices": [
            {"value": "true", "label": "Sí"},
            {"value": "false", "label": "No"},
        ],
    },
    {"name": "fecha_subida", "label": "Fecha de subida", "type": "date"},
]

DEFAULT_FIELD = "archivo"

IMPORTAREXPEDIENTE_ADVANCED_FILTER = AdvancedFilterEngine(
    field_map=FIELD_MAP,
    field_types=FIELD_TYPES,
    allowed_ops={
        "text": TEXT_OPS,
        "number": NUM_OPS,
        "boolean": BOOL_OPS,
        "date": DATE_OPS,
    },
)


def get_filters_ui_config() -> Dict[str, Any]:
    return deepcopy(
        {
            "fields": [dict(field) for field in FILTER_FIELDS],
            "defaultField": DEFAULT_FIELD,
            "operators": {
                "text": list(TEXT_OPS),
                "number": list(NUM_OPS),
                "boolean": list(BOOL_OPS),
                "date": list(DATE_OPS),
            },
        }
    )


__all__ = [
    "IMPORTAREXPEDIENTE_ADVANCED_FILTER",
    "FIELD_MAP",
    "FIELD_TYPES",
    "FILTER_FIELDS",
    "get_filters_ui_config",
]
