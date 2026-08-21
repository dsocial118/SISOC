"""Configuracion de filtros combinables para el listado de expedientes de pago."""

from typing import Any, Dict

VINCULO_CON_ADMISION = "vinculado"
VINCULO_SIN_ADMISION = "sin_admision"

VINCULO_CHOICES = [
    (VINCULO_CON_ADMISION, "Con admisión asignada"),
    (VINCULO_SIN_ADMISION, "Sin admisión asignada"),
]

FIELD_MAP: Dict[str, str] = {
    "expediente_pago": "expediente_pago",
    "expediente_convenio": "expediente_convenio",
    "num_expediente_admision": "admision__num_expediente",
    "vinculo_admision": "vinculo_admision",
    "mes_pago": "mes_pago",
    "ano": "ano",
}

FIELD_TYPES: Dict[str, str] = {
    "expediente_pago": "text",
    "expediente_convenio": "text",
    "num_expediente_admision": "text",
    "vinculo_admision": "choice",
    "mes_pago": "text",
    "ano": "text",
}

TEXT_OPS = ["contains", "ncontains", "eq", "ne", "empty"]
CHOICE_OPS = ["eq", "ne"]

FILTER_FIELDS = [
    {"name": "expediente_pago", "label": "Expediente de pago", "type": "text"},
    {"name": "expediente_convenio", "label": "Expediente del convenio", "type": "text"},
    {
        "name": "num_expediente_admision",
        "label": "Expediente de la admisión",
        "type": "text",
    },
    {"name": "vinculo_admision", "label": "Vínculo con la admisión", "type": "choice"},
    {"name": "mes_pago", "label": "Mes de pago", "type": "text"},
    {"name": "ano", "label": "Año", "type": "text"},
]


def get_filters_ui_config() -> Dict[str, Any]:
    """Devuelve la configuracion serializable para la UI."""

    fields = [dict(field) for field in FILTER_FIELDS]
    choices_by_field = {
        "vinculo_admision": [
            {"value": value, "label": label} for value, label in VINCULO_CHOICES
        ],
    }
    for field in fields:
        choices = choices_by_field.get(field["name"])
        if choices:
            field["choices"] = choices

    return {
        "fields": fields,
        "operators": {
            "text": list(TEXT_OPS),
            "choice": list(CHOICE_OPS),
        },
    }
