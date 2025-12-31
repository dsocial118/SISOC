"""Configuracion para filtros combinables en admisiones legales."""

from typing import Any, Dict

# --- Backend ---------------------------------------------------------------

FIELD_MAP: Dict[str, str] = {
    "comedor_id": "comedor__id",
    "tipo_admision": "tipo",
    "comedor_nombre": "comedor__nombre",
    "organizacion": "comedor__organizacion__nombre",
    "num_expediente": "num_expediente",
    "provincia": "comedor__provincia__nombre",
    "equipo_tecnico": "comedor__dupla__nombre",
    "estado": "estado_legales",
    "fecha_modificado": "modificado",
}

FIELD_TYPES: Dict[str, str] = {
    "comedor_id": "number",
    "tipo_admision": "choice",
    "comedor_nombre": "text",
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

# --- Frontend --------------------------------------------------------------

FILTER_FIELDS = [
    {"name": "comedor_id", "label": "ID de comedor", "type": "number"},
    {
        "name": "tipo_admision",
        "label": "Tipo de admisi\u00f3n",
        "type": "choice",
    },
    {"name": "comedor_nombre", "label": "Nombre del comedor", "type": "text"},
    {
        "name": "organizacion",
        "label": "Organizaci\u00f3n del comedor",
        "type": "text",
    },
    {
        "name": "num_expediente",
        "label": "N\u00b0 de expediente",
        "type": "text",
    },
    {"name": "provincia", "label": "Provincia", "type": "choice"},
    {
        "name": "equipo_tecnico",
        "label": "Equipo t\u00e9cnico",
        "type": "choice",
    },
    {
        "name": "estado",
        "label": "Estado de la admisi\u00f3n",
        "type": "choice",
    },
    {
        "name": "fecha_modificado",
        "label": "Fecha de \u00faltima modificaci\u00f3n",
        "type": "date",
    },
]


def get_filters_ui_config() -> Dict[str, Any]:
    """Configuracion serializable para la UI de filtros avanzados."""

    fields = [dict(field) for field in FILTER_FIELDS]

    try:
        from admisiones.models.admisiones import Admision
        from core.models import Provincia
        from duplas.models import Dupla

        choices_by_field = {
            "estado": [
                {"value": value, "label": label}
                for value, label in Admision.ESTADOS_LEGALES
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
