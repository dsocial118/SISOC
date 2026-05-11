"""Configuración de filtros combinables para dispositivos."""

from typing import Any, Dict

from dispositivos.models import Dispositivo

FIELD_MAP: Dict[str, str] = {
    "nombre_institucion": "nombre_institucion",
    "tipo_dispositivo": "tipo_dispositivo",
    "modalidad_funcionamiento": "modalidad_funcionamiento",
    "provincia": "provincia__nombre",
    "municipio": "municipio__nombre",
    "capacidad_total_plazas": "capacidad_total_plazas",
}

FIELD_TYPES: Dict[str, str] = {
    "nombre_institucion": "text",
    "tipo_dispositivo": "choice",
    "modalidad_funcionamiento": "choice",
    "provincia": "text",
    "municipio": "text",
    "capacidad_total_plazas": "choice",
}

TEXT_OPS = ["contains", "ncontains", "eq", "ne", "empty"]
NUM_OPS = ["eq", "ne", "gt", "lt", "empty"]
CHOICE_OPS = ["eq", "ne", "empty"]

FILTER_FIELDS = [
    {"name": "nombre_institucion", "label": "Institución", "type": "text"},
    {"name": "tipo_dispositivo", "label": "Tipo de dispositivo", "type": "choice"},
    {
        "name": "modalidad_funcionamiento",
        "label": "Modalidad de funcionamiento",
        "type": "choice",
    },
    {"name": "provincia", "label": "Provincia", "type": "text"},
    {"name": "municipio", "label": "Municipio", "type": "text"},
    {
        "name": "capacidad_total_plazas",
        "label": "Capacidad total de plazas",
        "type": "choice",
    },
]


def _choices_to_ui(choices):
    return [{"value": value, "label": label} for value, label in choices]


def get_filters_ui_config() -> Dict[str, Any]:
    fields = [dict(field) for field in FILTER_FIELDS]
    choices_by_field = {
        "tipo_dispositivo": Dispositivo.TipoDispositivo.choices,
        "modalidad_funcionamiento": Dispositivo.ModalidadFuncionamiento.choices,
        "capacidad_total_plazas": Dispositivo.CapacidadPlazas.choices,
    }
    for field in fields:
        choices = choices_by_field.get(field["name"])
        if choices:
            field["choices"] = _choices_to_ui(choices)

    return {
        "fields": fields,
        "operators": {
            "text": list(TEXT_OPS),
            "number": list(NUM_OPS),
            "choice": list(CHOICE_OPS),
        },
        "defaultOperators": {
            "text": "contains",
            "number": "eq",
            "choice": "eq",
        },
    }
