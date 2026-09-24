"""Filtros combinables para los listados de Ver Para Ser Libre.

Homogeneiza los buscadores con el resto del sistema. Cada listado conserva los
campos que ya buscaba y suma los que su tabla muestra.
"""

from copy import deepcopy
from typing import Any, Dict, List

from core.services.advanced_filters import AdvancedFilterEngine

TEXT_OPS = ["contains", "ncontains", "eq", "ne", "empty"]
NUM_OPS = ["eq", "ne", "gt", "lt", "empty"]
CHOICE_OPS = ["eq", "ne"]
BOOL_OPS = ["eq", "ne"]
DATE_OPS = ["eq", "ne", "gt", "lt", "gte", "lte", "empty"]

BOOL_CHOICES = [{"value": "true", "label": "Sí"}, {"value": "false", "label": "No"}]


def _engine(field_map, field_types):
    return AdvancedFilterEngine(
        field_map=field_map,
        field_types=field_types,
        allowed_ops={
            "text": TEXT_OPS,
            "number": NUM_OPS,
            "choice": CHOICE_OPS,
            "boolean": BOOL_OPS,
            "date": DATE_OPS,
        },
    )


def _config(fields: List[Dict[str, Any]], default_field: str) -> Dict[str, Any]:
    return deepcopy(
        {
            "fields": fields,
            "defaultField": default_field,
            "operators": {
                "text": list(TEXT_OPS),
                "number": list(NUM_OPS),
                "choice": list(CHOICE_OPS),
                "boolean": list(BOOL_OPS),
                "date": list(DATE_OPS),
            },
        }
    )


# --- Itinerarios -----------------------------------------------------------
# Cubre exactamente lo que resolvia el panel de filtros propio del listado
# (codigo, provincia, estado, referente, localidad y rango de fechas) mas las
# sedes, que la busqueda libre ya alcanzaba.
ITINERARIO_FIELD_MAP: Dict[str, str] = {
    "codigo": "codigo",
    "provincia": "provincia__nombre",
    "estado": "estado",
    "referente_nombre": "referente_nombre",
    "referente_apellido": "referente_apellido",
    "referente_email": "referente_email",
    "sede": "sedes__nombre",
    "sede_cueanexo": "sedes__cueanexo",
    "localidad": "sedes__localidad",
    "localidades_tentativas": "localidades_tentativas",
    "matricula_estimada": "matricula_estimada",
    "fecha_inicio": "fecha_inicio",
    "fecha_fin": "fecha_fin",
}

ITINERARIO_FIELD_TYPES: Dict[str, str] = {
    "codigo": "text",
    "provincia": "text",
    "estado": "choice",
    "referente_nombre": "text",
    "referente_apellido": "text",
    "referente_email": "text",
    "sede": "text",
    "sede_cueanexo": "text",
    "localidad": "text",
    "localidades_tentativas": "text",
    "matricula_estimada": "number",
    "fecha_inicio": "date",
    "fecha_fin": "date",
}

ITINERARIO_FILTER_FIELDS = [
    {"name": "codigo", "label": "Código", "type": "text"},
    {"name": "provincia", "label": "Provincia", "type": "text"},
    {"name": "estado", "label": "Estado", "type": "choice"},
    {"name": "referente_nombre", "label": "Referente (nombre)", "type": "text"},
    {"name": "referente_apellido", "label": "Referente (apellido)", "type": "text"},
    {"name": "referente_email", "label": "Referente (email)", "type": "text"},
    {"name": "sede", "label": "Sede (nombre)", "type": "text"},
    {"name": "sede_cueanexo", "label": "Sede (CUE anexo)", "type": "text"},
    {"name": "localidad", "label": "Localidad", "type": "text"},
    {
        "name": "localidades_tentativas",
        "label": "Localidades tentativas",
        "type": "text",
    },
    {"name": "matricula_estimada", "label": "Matrícula estimada", "type": "number"},
    {"name": "fecha_inicio", "label": "Fecha de inicio", "type": "date"},
    {"name": "fecha_fin", "label": "Fecha de fin", "type": "date"},
]

ITINERARIO_ADVANCED_FILTER = _engine(ITINERARIO_FIELD_MAP, ITINERARIO_FIELD_TYPES)


def get_itinerario_filters_ui_config() -> Dict[str, Any]:
    from ver_para_ser_libre.models import ItinerarioVPSL

    fields = [dict(field) for field in ITINERARIO_FILTER_FIELDS]
    for field in fields:
        if field["name"] == "estado":
            field["choices"] = [
                {"value": valor, "label": etiqueta}
                for valor, etiqueta in ItinerarioVPSL._meta.get_field("estado").choices
            ]
    return _config(fields, "codigo")


# --- Sedes -----------------------------------------------------------------
SEDE_FIELD_MAP: Dict[str, str] = {
    "nombre": "nombre",
    "cueanexo": "cueanexo",
    "jurisdiccion": "jurisdiccion",
    "localidad": "localidad",
    "domicilio": "domicilio",
    "departamento": "departamento",
    "sector": "sector",
    "ambito": "ambito",
    "codigo_postal": "codigo_postal",
    "telefono": "telefono",
    "mail": "mail",
    "checklist_aprobado": "checklist_aprobado",
}

SEDE_FIELD_TYPES: Dict[str, str] = {
    "nombre": "text",
    "cueanexo": "text",
    "jurisdiccion": "text",
    "localidad": "text",
    "domicilio": "text",
    "departamento": "text",
    "sector": "text",
    "ambito": "text",
    "codigo_postal": "text",
    "telefono": "text",
    "mail": "text",
    "checklist_aprobado": "boolean",
}

SEDE_FILTER_FIELDS = [
    {"name": "nombre", "label": "Nombre", "type": "text"},
    {"name": "cueanexo", "label": "CUE anexo", "type": "text"},
    {"name": "jurisdiccion", "label": "Jurisdicción", "type": "text"},
    {"name": "localidad", "label": "Localidad", "type": "text"},
    {"name": "domicilio", "label": "Domicilio", "type": "text"},
    {"name": "departamento", "label": "Departamento", "type": "text"},
    {"name": "sector", "label": "Sector", "type": "text"},
    {"name": "ambito", "label": "Ámbito", "type": "text"},
    {"name": "codigo_postal", "label": "Código postal", "type": "text"},
    {"name": "telefono", "label": "Teléfono", "type": "text"},
    {"name": "mail", "label": "Mail", "type": "text"},
    {
        "name": "checklist_aprobado",
        "label": "Checklist aprobado?",
        "type": "boolean",
        "choices": BOOL_CHOICES,
    },
]

SEDE_ADVANCED_FILTER = _engine(SEDE_FIELD_MAP, SEDE_FIELD_TYPES)


def get_sede_filters_ui_config() -> Dict[str, Any]:
    return _config([dict(f) for f in SEDE_FILTER_FIELDS], "nombre")


__all__ = [
    "ITINERARIO_ADVANCED_FILTER",
    "SEDE_ADVANCED_FILTER",
    "get_itinerario_filters_ui_config",
    "get_sede_filters_ui_config",
]
