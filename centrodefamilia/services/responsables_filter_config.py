"""Configuración para filtros combinables de responsables."""

from typing import Dict

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
            "genero",
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
    **{
        key: "number"
        for key in [
            "dni",
            "cuil",
            "codigo_postal",
            "altura",
            "cantidad_beneficiarios",
        ]
    },
}

TEXT_OPS = {"contains", "ncontains", "eq", "ne", "empty"}
NUM_OPS = {"eq", "ne", "gt", "lt", "empty"}

__all__ = ["FIELD_MAP", "FIELD_TYPES", "TEXT_OPS", "NUM_OPS"]
