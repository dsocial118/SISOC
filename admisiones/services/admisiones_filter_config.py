"""Configuracion para filtros combinables en admisiones tecnicos."""

from typing import Any, Dict

# --- Backend ---------------------------------------------------------------

FIELD_MAP: Dict[str, str] = {
    "comedor_nombre": "comedor__nombre",
    "comedor_id": "comedor__id",
    "estado_legales": "estado_legales",
    "fecha_modificado": "modificado",
    "num_expediente": "num_expediente",
    "tipo_convenio": "tipo_convenio__nombre",
}

FIELD_TYPES: Dict[str, str] = {
    "comedor_nombre": "text",
    "comedor_id": "number",
    "estado_legales": "choice",
    "fecha_modificado": "date",
    "num_expediente": "text",
    "tipo_convenio": "choice",
}

TEXT_OPS = ["contains", "ncontains", "eq", "ne", "empty"]
NUM_OPS = ["eq", "ne", "gt", "lt", "empty"]
DATE_OPS = ["eq", "ne", "gt", "lt", "empty"]
CHOICE_OPS = ["eq", "ne"]

# --- Frontend --------------------------------------------------------------

FILTER_FIELDS = [
    {"name": "comedor_nombre", "label": "Nombre del comedor", "type": "text"},
    {"name": "comedor_id", "label": "ID del comedor", "type": "number"},
    {
        "name": "estado_legales",
        "label": "Estado legales de la admision",
        "type": "choice",
    },
    {
        "name": "fecha_modificado",
        "label": "Fecha ultima modificacion de la admision",
        "type": "date",
    },
    {
        "name": "num_expediente",
        "label": "Numero de expediente de la admision",
        "type": "text",
    },
    {
        "name": "tipo_convenio",
        "label": "Tipo de convenio de la admision",
        "type": "choice",
    },
]


def get_filters_ui_config() -> Dict[str, Any]:
    """Configuracion serializable para la UI de filtros avanzados."""

    fields = [dict(field) for field in FILTER_FIELDS]

    try:
        from admisiones.models.admisiones import Admision, TipoConvenio

        choices_by_field = {
            "estado_legales": [
                {"value": value, "label": label}
                for value, label in Admision.ESTADOS_LEGALES
            ],
            "tipo_convenio": [
                {"value": value, "label": value}
                for value in TipoConvenio.objects.order_by("nombre")
                .values_list("nombre", flat=True)
                if value
            ],
        }

        for field in fields:
            name = field.get("name")
            if name in choices_by_field and choices_by_field[name]:
                field["choices"] = choices_by_field[name]
    except Exception:
        # Si falla la carga del modelo, se devuelven los campos base sin choices.
        pass

    return {
        "fields": fields,
        "operators": {
            "text": list(TEXT_OPS),
            "number": list(NUM_OPS),
            "date": list(DATE_OPS),
            "choice": list(CHOICE_OPS),
        },
    }


__all__ = [
    "FIELD_MAP",
    "FIELD_TYPES",
    "TEXT_OPS",
    "NUM_OPS",
    "DATE_OPS",
    "CHOICE_OPS",
    "FILTER_FIELDS",
    "get_filters_ui_config",
]
