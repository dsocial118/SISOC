"""Configuración para filtros combinables de beneficiarios."""

from typing import Dict

FIELD_MAP: Dict[str, str] = {
    "username": "username",
    "email": "email",
    "first_name": "first_name",
    "last_name": "last_name",
    "rol": "rol",
}

FIELD_TYPES: Dict[str, str] = {
    **{key: "text" for key in [
        "username",
        "email",
        "first_name",
        "last_name",
        "rol",
    ]},
    **{key: "number" for key in [
        "dni"
    ]},
}

TEXT_OPS = {"contains", "ncontains", "eq", "ne", "empty"}
NUM_OPS = {"eq", "ne", "gt", "lt", "empty"}

__all__ = ["FIELD_MAP", "FIELD_TYPES", "TEXT_OPS", "NUM_OPS"]