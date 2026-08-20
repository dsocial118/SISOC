"""Configuracion de filtros combinables para el listado de acompanamientos."""

import logging

from typing import Any, Dict

logger = logging.getLogger(__name__)


# El listado tiene una fila por acompañamiento, por lo que la base del queryset
# es Admision y los campos del comedor se alcanzan por la relación.
FIELD_MAP: Dict[str, str] = {
    "comedor_nombre": "comedor__nombre",
    "comedor_id": "comedor__id",
    "tipo_admision": "tipo",
    "organizacion": "comedor__organizacion__nombre",
    "num_expediente": "num_expediente",
    "provincia": "comedor__provincia__nombre",
    "equipo_tecnico": "comedor__dupla__nombre",
    "estado": "estado_admision",
    "estado_acompanamiento": "estado_acompanamiento",
    "fecha_modificado": "modificado",
}

FIELD_TYPES: Dict[str, str] = {
    "comedor_nombre": "text",
    "comedor_id": "number",
    "tipo_admision": "choice",
    "organizacion": "text",
    "num_expediente": "text",
    "provincia": "choice",
    "equipo_tecnico": "choice",
    "estado": "choice",
    "estado_acompanamiento": "choice",
    "fecha_modificado": "date",
}

TEXT_OPS = ["contains", "ncontains", "eq", "ne", "empty"]
NUM_OPS = ["eq", "ne", "gt", "lt", "empty"]
DATE_OPS = ["eq", "ne", "gt", "lt", "empty"]
CHOICE_OPS = ["eq", "ne"]

FILTER_FIELDS = [
    {"name": "comedor_nombre", "label": "Nombre del comedor", "type": "text"},
    {"name": "comedor_id", "label": "ID de comedor", "type": "number"},
    {"name": "tipo_admision", "label": "Tipo de admisión", "type": "choice"},
    {"name": "organizacion", "label": "Organización del comedor", "type": "text"},
    {"name": "num_expediente", "label": "N° de expediente", "type": "text"},
    {"name": "provincia", "label": "Provincia", "type": "choice"},
    {"name": "equipo_tecnico", "label": "Equipo técnico", "type": "choice"},
    {"name": "estado", "label": "Estado de la admisión", "type": "choice"},
    {
        "name": "estado_acompanamiento",
        "label": "Estado del acompañamiento",
        "type": "choice",
    },
    {
        "name": "fecha_modificado",
        "label": "Fecha de última modificación",
        "type": "date",
    },
]


def get_filters_ui_config() -> Dict[str, Any]:
    """Devuelve la configuracion serializable para la UI."""

    from acompanamientos.models.acompanamiento import Acompanamiento
    from admisiones.models.admisiones import Admision

    fields = [dict(field) for field in FILTER_FIELDS]

    # Choices estáticas: no dependen de la base, así que se resuelven aparte para
    # que un problema de consulta no se lleve puestas también a estas.
    choices_by_field = {
        "estado": [
            {"value": value, "label": label}
            for value, label in Admision.ESTADOS_ADMISION
        ],
        "estado_acompanamiento": [
            {"value": value, "label": label} for value, label in Acompanamiento.ESTADOS
        ],
        "tipo_admision": [
            {"value": value, "label": label} for value, label in Admision.TIPO_ADMISION
        ],
    }

    try:
        from core.models import Provincia
        from duplas.models import Dupla

        choices_by_field["provincia"] = [
            {"value": value, "label": value}
            for value in Provincia.objects.order_by("nombre").values_list(
                "nombre", flat=True
            )
            if value
        ]
        choices_by_field["equipo_tecnico"] = [
            {"value": value, "label": value}
            for value in Dupla.objects.activas().values_list("nombre", flat=True)
            if value
        ]
    except Exception:
        logger.exception(
            "No se pudieron cargar las opciones de filtros de acompanamientos"
        )

    for field in fields:
        choices = choices_by_field.get(field["name"])
        if choices:
            field["choices"] = choices

    return {
        "fields": fields,
        "operators": {
            "text": list(TEXT_OPS),
            "number": list(NUM_OPS),
            "date": list(DATE_OPS),
            "choice": list(CHOICE_OPS),
        },
    }
