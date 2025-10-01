"""Configuración para filtros combinables de beneficiarios."""

from typing import Dict

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
            "genero",
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
    **{
        key: "number"
        for key in [
            "dni",
            "cuil",
            "codigo_postal",
            "altura",
        ]
    },
}

TEXT_OPS = {"contains", "ncontains", "eq", "ne", "empty"}
NUM_OPS = {"eq", "ne", "gt", "lt", "empty"}

__all__ = ["FIELD_MAP", "FIELD_TYPES", "TEXT_OPS", "NUM_OPS"]
