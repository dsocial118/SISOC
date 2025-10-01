"""Configuración para filtros combinables de centros."""

from typing import Dict

FIELD_MAP: Dict[str, str] = {
    "nombre": "nombre",
    "tipo": "tipo",
    "faro_asociado": "faro_asociado__nombre",
    "codigo": "codigo",
    "organizacion_asociada": "organizacion_asociada__nombre",
    "provincia": "provincia__nombre",
    "municipio": "municipio__nombre",
    "localidad": "localidad__nombre",
    "calle": "calle",
    "numero": "numero",
    "domicilio_actividad": "domicilio_actividad",
    "telefono": "telefono",
    "celular": "celular",
    "correo": "correo",
    "sitio_web": "sitio_web",
    "link_redes": "link_redes",
    "nombre_referente": "nombre_referente",
    "apellido_referente": "apellido_referente",
    "telefono_referente": "telefono_referente",
    "correo_referente": "correo_referente",
    "activo": "activo",
}

FIELD_TYPES: Dict[str, str] = {
    **{
        key: "text"
        for key in [
            "nombre",
            "tipo",
            "faro_asociado",
            "organizacion_asociada",
            "provincia",
            "municipio",
            "localidad",
            "calle",
            "domicilio_actividad",
            "telefono",
            "celular",
            "correo",
            "sitio_web",
            "link_redes",
            "nombre_referente",
            "apellido_referente",
            "telefono_referente",
            "correo_referente",
        ]
    },
    **{
        key: "number"
        for key in [
            "numero",
        ]
    },
    **{
        key: "boolean"
        for key in [
            "activo",
        ]
    },
}

TEXT_OPS = {"contains", "ncontains", "eq", "ne", "empty"}
NUM_OPS = {"eq", "ne", "gt", "lt", "empty"}
BOOL_OPS = {"eq", "ne"}

__all__ = ["FIELD_MAP", "FIELD_TYPES", "TEXT_OPS", "NUM_OPS", "BOOL_OPS"]
