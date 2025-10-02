"""Configuración para filtros combinables de responsables."""

from typing import Any, Dict

FIELD_MAP: Dict[str, str] = {
    "apellido": "apellido",
    "nombre": "nombre",
    "genero": "genero",
    "vinculo_parental": "vinculo_parental",
    "correo_electronico": "correo_electronico",
    "barrio": "barrio",
    "calle": "calle",
    "provincia": "provincia__nombre",
    "municipio": "municipio__nombre",
    "localidad": "localidad__nombre",
    "prefijo_celular": "prefijo_celular",
    "numero_celular": "numero_celular",
    "prefijo_telefono_fijo": "prefijo_telefono_fijo",
    "numero_telefono_fijo": "numero_telefono_fijo",
    "monoblock": "monoblock",
    "dni": "dni",
    "cuil": "cuil",
    "codigo_postal": "codigo_postal",
    "altura": "altura",
    "cantidad_beneficiarios": "cantidad_beneficiarios",
}

FIELD_TYPES: Dict[str, str] = {
    **{
        key: "text"
        for key in [
            "apellido",
            "nombre",
            "vinculo_parental",
            "correo_electronico",
            "barrio",
            "calle",
            "provincia",
            "municipio",
            "localidad",
            "prefijo_celular",
            "numero_celular",
            "prefijo_telefono_fijo",
            "numero_telefono_fijo",
            "monoblock",
        ]
    },
    "genero": "choice",
    **{
        key: "number"
        for key in ["dni", "cuil", "codigo_postal", "altura", "cantidad_beneficiarios"]
    },
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
    {
        "name": "vinculo_parental",
        "label": "Vínculo parental",
        "type": "text",
    },
    {
        "name": "correo_electronico",
        "label": "Correo electrónico",
        "type": "text",
    },
    {"name": "barrio", "label": "Barrio", "type": "text"},
    {"name": "calle", "label": "Calle", "type": "text"},
    {"name": "provincia", "label": "Provincia", "type": "text"},
    {"name": "municipio", "label": "Municipio", "type": "text"},
    {"name": "localidad", "label": "Localidad", "type": "text"},
    {
        "name": "prefijo_celular",
        "label": "Prefijo celular",
        "type": "text",
    },
    {
        "name": "numero_celular",
        "label": "Número celular",
        "type": "text",
    },
    {
        "name": "prefijo_telefono_fijo",
        "label": "Prefijo teléfono fijo",
        "type": "text",
    },
    {
        "name": "numero_telefono_fijo",
        "label": "Número teléfono fijo",
        "type": "text",
    },
    {"name": "monoblock", "label": "Monoblock", "type": "text"},
    {"name": "dni", "label": "DNI", "type": "number"},
    {"name": "cuil", "label": "CUIL", "type": "number"},
    {
        "name": "codigo_postal",
        "label": "Código postal",
        "type": "number",
    },
    {"name": "altura", "label": "Altura", "type": "number"},
    {
        "name": "cantidad_beneficiarios",
        "label": "Cantidad de beneficiarios",
        "type": "number",
    },
]


def get_filters_ui_config() -> Dict[str, Any]:
    """Devuelve la configuración consumida por la barra de filtros."""

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
