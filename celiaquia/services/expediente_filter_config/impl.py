"""Configuración de filtros combinables para el listado de expedientes.

Los campos expuestos siguen las columnas de la grilla para que el usuario filtre
por lo mismo que ve. ``provincia`` apunta a la anotación ``provincia_derivada``
del queryset (y no a un join con los legajos) porque el expediente no tiene
provincia propia: se deriva de sus ciudadanos, con respaldo en el perfil legacy
del usuario creador.
"""

from typing import Any, Dict

# Mapea el identificador expuesto en la UI -> lookup real del ORM.
FIELD_MAP: Dict[str, str] = {
    "id": "id",
    "numero_expediente": "numero_expediente",
    "fecha_creacion": "fecha_creacion__date",
    "provincia": "provincia_derivada",
    "estado": "estado__nombre",
    "tecnico": "asignaciones_tecnicos__tecnico__username",
}

FIELD_TYPES: Dict[str, str] = {
    "id": "number",
    "numero_expediente": "text",
    "fecha_creacion": "date",
    "provincia": "choice",
    "estado": "choice",
    "tecnico": "choice",
}

TEXT_OPS = ["contains", "ncontains", "eq", "ne", "empty"]
NUM_OPS = ["eq", "ne", "gt", "lt", "empty"]
DATE_OPS = ["eq", "ne", "gt", "lt", "empty"]
CHOICE_OPS = ["eq", "ne", "empty"]

FILTER_FIELDS = [
    {"name": "id", "label": "ID", "type": "number"},
    {"name": "numero_expediente", "label": "Número de expediente", "type": "text"},
    {"name": "fecha_creacion", "label": "Fecha de creación", "type": "date"},
    {"name": "provincia", "label": "Provincia", "type": "choice"},
    {"name": "estado", "label": "Estado", "type": "choice"},
    {"name": "tecnico", "label": "Técnico asignado", "type": "choice"},
]


def _estado_choices():
    from celiaquia.models import (  # pylint: disable=import-outside-toplevel
        EstadoExpediente,
    )

    return [
        {"value": estado.nombre, "label": estado.display_name()}
        for estado in EstadoExpediente.objects.order_by("nombre")
    ]


def _provincia_choices():
    from core.models import Provincia  # pylint: disable=import-outside-toplevel

    return [
        {"value": nombre, "label": nombre}
        for nombre in Provincia.objects.order_by("nombre").values_list(
            "nombre", flat=True
        )
        if nombre
    ]


def _tecnico_choices(tecnicos):
    return [
        {
            "value": tecnico.username,
            "label": tecnico.get_full_name() or tecnico.username,
        }
        for tecnico in tecnicos
    ]


def get_filters_ui_config(*, tecnicos=None) -> Dict[str, Any]:
    """Configuración serializable para la UI de filtros combinables.

    ``tecnicos`` es el listado de técnicos seleccionables. Si viene vacío o en
    ``None`` el campo "Técnico asignado" no se ofrece, de modo que quien no ve la
    columna de técnico tampoco pueda filtrar por ella.
    """

    choices_by_field = {
        "estado": _estado_choices(),
        "provincia": _provincia_choices(),
        "tecnico": _tecnico_choices(tecnicos or []),
    }

    fields = []
    for field in FILTER_FIELDS:
        name = field["name"]
        choices = choices_by_field.get(name)
        if field["type"] == "choice":
            if not choices:
                continue
            field = {**field, "choices": choices}
        else:
            field = dict(field)
        fields.append(field)

    return {
        "fields": fields,
        "operators": {
            "text": list(TEXT_OPS),
            "number": list(NUM_OPS),
            "date": list(DATE_OPS),
            "choice": list(CHOICE_OPS),
        },
        "defaultOperators": {
            "text": "contains",
            "number": "eq",
            "date": "eq",
            "choice": "eq",
        },
    }


__all__ = [
    "CHOICE_OPS",
    "DATE_OPS",
    "FIELD_MAP",
    "FIELD_TYPES",
    "FILTER_FIELDS",
    "NUM_OPS",
    "TEXT_OPS",
    "get_filters_ui_config",
]
