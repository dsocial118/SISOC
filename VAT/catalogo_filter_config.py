"""Filtros combinables para los catalogos de VAT.

Homogeneiza los buscadores de los listados (mismo componente y mismo motor que
comedores, dispositivos, celiaquia, etc.). Cada catalogo conserva lo que ya
buscaba y suma los campos que su listado muestra en pantalla.
"""

from copy import deepcopy
from typing import Any, Dict, List

from core.services.advanced_filters import AdvancedFilterEngine

TEXT_OPS = ["contains", "ncontains", "eq", "ne", "empty"]
NUM_OPS = ["eq", "ne", "gt", "lt", "empty"]
CHOICE_OPS = ["eq", "ne"]
BOOL_OPS = ["eq", "ne"]

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
            },
        }
    )


# --- Modalidad de cursado --------------------------------------------------
# Antes el listado no filtraba nada: el buscador se renderizaba pero la vista
# ignoraba `busqueda`. Ahora busca de verdad sobre lo que muestra la tabla.
MODALIDAD_FIELD_MAP: Dict[str, str] = {
    "nombre": "nombre",
    "descripcion": "descripcion",
    "activo": "activo",
}

MODALIDAD_FIELD_TYPES: Dict[str, str] = {
    "nombre": "text",
    "descripcion": "text",
    "activo": "boolean",
}

MODALIDAD_FILTER_FIELDS = [
    {"name": "nombre", "label": "Nombre", "type": "text"},
    {"name": "descripcion", "label": "Descripción", "type": "text"},
    {
        "name": "activo",
        "label": "Activa?",
        "type": "boolean",
        "choices": BOOL_CHOICES,
    },
]

MODALIDAD_ADVANCED_FILTER = _engine(MODALIDAD_FIELD_MAP, MODALIDAD_FIELD_TYPES)


def get_modalidad_filters_ui_config() -> Dict[str, Any]:
    return _config([dict(f) for f in MODALIDAD_FILTER_FIELDS], "nombre")


# --- Plan / version curricular ---------------------------------------------
# Conserva los filtros propios del listado (titulo y activo) y agrega los
# campos que la tabla ya mostraba: sector, subsector y modalidad.
PLAN_FIELD_MAP: Dict[str, str] = {
    "nombre": "nombre",
    "sector": "sector__nombre",
    "subsector": "subsector__nombre",
    "modalidad_cursada": "modalidad_cursada__nombre",
    "titulo": "titulos__nombre",
    "normativa": "normativa",
    "nivel_requerido": "nivel_requerido",
    "nivel_certifica": "nivel_certifica",
    "provincia": "provincia__nombre",
    "horas_reloj": "horas_reloj",
    "activo": "activo",
}

PLAN_FIELD_TYPES: Dict[str, str] = {
    "nombre": "text",
    "sector": "text",
    "subsector": "text",
    "modalidad_cursada": "text",
    "titulo": "text",
    "normativa": "text",
    "nivel_requerido": "text",
    "nivel_certifica": "text",
    "provincia": "text",
    "horas_reloj": "number",
    "activo": "boolean",
}

PLAN_FILTER_FIELDS = [
    {"name": "nombre", "label": "Nombre", "type": "text"},
    {"name": "sector", "label": "Sector", "type": "text"},
    {"name": "subsector", "label": "Subsector", "type": "text"},
    {"name": "modalidad_cursada", "label": "Modalidad de cursado", "type": "text"},
    {"name": "titulo", "label": "Título de referencia", "type": "text"},
    {"name": "normativa", "label": "Normativa", "type": "text"},
    {"name": "nivel_requerido", "label": "Nivel requerido", "type": "text"},
    {"name": "nivel_certifica", "label": "Nivel que certifica", "type": "text"},
    {"name": "provincia", "label": "Provincia", "type": "text"},
    {"name": "horas_reloj", "label": "Horas reloj", "type": "number"},
    {
        "name": "activo",
        "label": "Activo?",
        "type": "boolean",
        "choices": BOOL_CHOICES,
    },
]

PLAN_ADVANCED_FILTER = _engine(PLAN_FIELD_MAP, PLAN_FIELD_TYPES)


def get_plan_filters_ui_config() -> Dict[str, Any]:
    return _config([dict(f) for f in PLAN_FILTER_FIELDS], "nombre")


__all__ = [
    "MODALIDAD_ADVANCED_FILTER",
    "PLAN_ADVANCED_FILTER",
    "get_modalidad_filters_ui_config",
    "get_plan_filters_ui_config",
]
