"""Configuración para filtros combinables de beneficiarios."""

from typing import Any, Dict

FIELD_MAP: Dict[str, str] = {
    "apellido": "apellido",
    "nombre": "nombre",
    "genero": "genero",
    "domicilio": "domicilio",
    "barrio": "barrio",
    "correo_electronico": "correo_electronico",
    "responsable_apellido": "responsable__apellido",
    "responsable_nombre": "responsable__nombre",
    "provincia": "provincia__nombre",
    "municipio": "municipio__nombre",
    "localidad": "localidad__nombre",
    "dni": "dni",
    "cuil": "cuil",
    "codigo_postal": "codigo_postal",
    "altura": "altura",
}

FIELD_TYPES: Dict[str, str] = {
    **{
        key: "text"
        for key in [
            "apellido",
            "nombre",
            "domicilio",
            "barrio",
            "correo_electronico",
            "responsable_apellido",
            "responsable_nombre",
            "provincia",
            "municipio",
            "localidad",
        ]
    },
    "genero": "choice",
    **{key: "number" for key in ["dni", "cuil", "codigo_postal", "altura"]},
}

TEXT_OPS = ["contains", "ncontains", "eq", "ne", "empty"]
NUM_OPS = ["eq", "ne", "gt", "lt", "empty"]
CHOICE_OPS = ["eq", "ne"]

FILTER_FIELDS = [
    {"name": "apellido", "label": "Apellido", "type": "text"},
    {"name": "nombre", "label": "Nombre", "type": "text"},
    {
        "name": "genero",
        "label": "Género",
        "type": "choice",
        "choices": [
            {"value": "F", "label": "Femenino"},
            {"value": "M", "label": "Masculino"},
            {"value": "X", "label": "Otro/No binario"},
        ],
    },
    {"name": "domicilio", "label": "Domicilio", "type": "text"},
    {"name": "barrio", "label": "Barrio", "type": "text"},
    {
        "name": "correo_electronico",
        "label": "Correo electrónico",
        "type": "text",
    },
    {
        "name": "responsable_apellido",
        "label": "Apellido del responsable",
        "type": "text",
    },
    {
        "name": "responsable_nombre",
        "label": "Nombre del responsable",
        "type": "text",
    },
    {"name": "provincia", "label": "Provincia", "type": "text"},
    {"name": "municipio", "label": "Municipio", "type": "text"},
    {"name": "localidad", "label": "Localidad", "type": "text"},
    {"name": "dni", "label": "DNI", "type": "number"},
    {"name": "cuil", "label": "CUIL", "type": "number"},
    {
        "name": "codigo_postal",
        "label": "Código postal",
        "type": "number",
    },
    {"name": "altura", "label": "Altura", "type": "number"},
]


def get_filters_ui_config() -> Dict[str, Any]:
    """Devuelve la definición de filtros para la barra combinable."""

    return {
        "fields": FILTER_FIELDS,
        "operators": {
            "text": list(TEXT_OPS),
            "number": list(NUM_OPS),
            "choice": list(CHOICE_OPS),
        },
    }


__all__ = [
    "FIELD_MAP",
    "FIELD_TYPES",
    "TEXT_OPS",
    "NUM_OPS",
    "CHOICE_OPS",
    "FILTER_FIELDS",
    "get_filters_ui_config",
]
