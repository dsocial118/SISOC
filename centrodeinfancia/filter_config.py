"""Filtros combinables para el listado de Centros de Desarrollo Infantil.

Conserva lo que ya buscaba el listado (nombre y organizacion) y suma los campos
que la tabla muestra: codigo, ubicacion, ambito, jornada y gestion.
"""

from copy import deepcopy
from typing import Any, Dict

from core.services.advanced_filters import AdvancedFilterEngine

FIELD_MAP: Dict[str, str] = {
    "nombre": "nombre",
    "codigo_cdi": "codigo_cdi",
    "organizacion": "organizacion",
    "cuit_organizacion_gestiona": "cuit_organizacion_gestiona",
    "provincia": "provincia__nombre",
    "departamento": "departamento__nombre",
    "municipio": "municipio__nombre",
    "localidad": "localidad__nombre",
    "calle": "calle",
    "ambito": "ambito",
    "tipo_jornada": "tipo_jornada",
    "modalidad_gestion": "modalidad_gestion",
    "nombre_referente": "nombre_referente",
    "apellido_referente": "apellido_referente",
    "mail": "mail",
    "telefono": "telefono",
    "codigo_postal": "codigo_postal",
    "fecha_inicio": "fecha_inicio",
}

FIELD_TYPES: Dict[str, str] = {
    **{
        k: "text"
        for k in [
            "nombre",
            "codigo_cdi",
            "organizacion",
            "cuit_organizacion_gestiona",
            "provincia",
            "departamento",
            "municipio",
            "localidad",
            "calle",
            "nombre_referente",
            "apellido_referente",
            "mail",
            "telefono",
        ]
    },
    **{k: "choice" for k in ["ambito", "tipo_jornada", "modalidad_gestion"]},
    "codigo_postal": "number",
    "fecha_inicio": "date",
}

TEXT_OPS = ["contains", "ncontains", "eq", "ne", "empty"]
NUM_OPS = ["eq", "ne", "gt", "lt", "empty"]
CHOICE_OPS = ["eq", "ne"]
DATE_OPS = ["eq", "ne", "gt", "lt", "gte", "lte", "empty"]

FILTER_FIELDS = [
    {"name": "nombre", "label": "Nombre", "type": "text"},
    {"name": "codigo_cdi", "label": "Código CDI", "type": "text"},
    {"name": "organizacion", "label": "Organización", "type": "text"},
    {
        "name": "cuit_organizacion_gestiona",
        "label": "CUIT de la organización",
        "type": "text",
    },
    {"name": "provincia", "label": "Provincia", "type": "text"},
    {"name": "departamento", "label": "Departamento", "type": "text"},
    {"name": "municipio", "label": "Municipio", "type": "text"},
    {"name": "localidad", "label": "Localidad", "type": "text"},
    {"name": "calle", "label": "Calle", "type": "text"},
    {"name": "ambito", "label": "Ámbito", "type": "choice"},
    {"name": "tipo_jornada", "label": "Tipo de jornada", "type": "choice"},
    {"name": "modalidad_gestion", "label": "Modalidad de gestión", "type": "choice"},
    {"name": "nombre_referente", "label": "Referente (nombre)", "type": "text"},
    {"name": "apellido_referente", "label": "Referente (apellido)", "type": "text"},
    {"name": "mail", "label": "Mail", "type": "text"},
    {"name": "telefono", "label": "Teléfono", "type": "text"},
    {"name": "codigo_postal", "label": "Código postal", "type": "number"},
    {"name": "fecha_inicio", "label": "Fecha de inicio", "type": "date"},
]

DEFAULT_FIELD = "nombre"

CENTRODEINFANCIA_ADVANCED_FILTER = AdvancedFilterEngine(
    field_map=FIELD_MAP,
    field_types=FIELD_TYPES,
    allowed_ops={
        "text": TEXT_OPS,
        "number": NUM_OPS,
        "choice": CHOICE_OPS,
        "date": DATE_OPS,
    },
)


def get_filters_ui_config() -> Dict[str, Any]:
    from centrodeinfancia.models import CentroDeInfancia

    fields = [dict(field) for field in FILTER_FIELDS]
    choices_por_campo = {
        campo: CentroDeInfancia._meta.get_field(campo).choices
        for campo in ("ambito", "tipo_jornada", "modalidad_gestion")
    }
    for field in fields:
        choices = choices_por_campo.get(field["name"])
        if choices:
            field["choices"] = [
                {"value": valor, "label": etiqueta} for valor, etiqueta in choices
            ]

    return deepcopy(
        {
            "fields": fields,
            "defaultField": DEFAULT_FIELD,
            "operators": {
                "text": list(TEXT_OPS),
                "number": list(NUM_OPS),
                "choice": list(CHOICE_OPS),
                "date": list(DATE_OPS),
            },
        }
    )


__all__ = [
    "CENTRODEINFANCIA_ADVANCED_FILTER",
    "FIELD_MAP",
    "FIELD_TYPES",
    "FILTER_FIELDS",
    "get_filters_ui_config",
]
