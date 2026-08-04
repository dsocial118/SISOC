"""Configuracion de filtros combinables para el listado de acompanamientos."""

from typing import Any, Dict

FIELD_MAP: Dict[str, str] = {
    "comedor_nombre": "nombre",
    "comedor_id": "id",
    "tipo_admision": "admision__tipo",
    "organizacion": "organizacion__nombre",
    "num_expediente": "admision__num_expediente",
    "provincia": "provincia__nombre",
    "equipo_tecnico": "dupla__nombre",
    "estado": "admision__estado_admision",
    "fecha_modificado": "admision__modificado",
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
        "name": "fecha_modificado",
        "label": "Fecha de última modificación",
        "type": "date",
    },
]


def get_filters_ui_config() -> Dict[str, Any]:
    """Devuelve la configuracion serializable para la UI."""

    fields = [dict(field) for field in FILTER_FIELDS]
    try:
        from admisiones.models.admisiones import Admision
        from core.models import Provincia
        from duplas.models import Dupla

        choices_by_field = {
            "estado": [
                {"value": value, "label": label}
                for value, label in Admision.ESTADOS_ADMISION
            ],
            "tipo_admision": [
                {"value": value, "label": label}
                for value, label in Admision.TIPO_ADMISION
            ],
            "provincia": [
                {"value": value, "label": value}
                for value in Provincia.objects.order_by("nombre").values_list(
                    "nombre", flat=True
                )
                if value
            ],
            "equipo_tecnico": [
                {"value": value, "label": value}
                for value in Dupla.objects.activas().values_list("nombre", flat=True)
                if value
            ],
        }
        for field in fields:
            choices = choices_by_field.get(field["name"])
            if choices:
                field["choices"] = choices
    except Exception:
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
