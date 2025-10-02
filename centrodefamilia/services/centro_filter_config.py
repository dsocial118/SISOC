"""Configuración para filtros combinables de centros."""

from typing import Any, Dict

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

TEXT_OPS = ["contains", "ncontains", "eq", "ne", "empty"]
NUM_OPS = ["eq", "ne", "gt", "lt", "empty"]
BOOL_OPS = ["eq", "ne"]

FILTER_FIELDS = [
    {"name": "nombre", "label": "Nombre", "type": "text"},
    {"name": "tipo", "label": "Tipo", "type": "text"},
    {"name": "faro_asociado", "label": "Faro asociado", "type": "text"},
    {"name": "codigo", "label": "Código", "type": "text"},
    {
        "name": "organizacion_asociada",
        "label": "Organización asociada",
        "type": "text",
    },
    {"name": "provincia", "label": "Provincia", "type": "text"},
    {"name": "municipio", "label": "Municipio", "type": "text"},
    {"name": "localidad", "label": "Localidad", "type": "text"},
    {"name": "calle", "label": "Calle", "type": "text"},
    {"name": "numero", "label": "Número", "type": "number"},
    {
        "name": "domicilio_actividad",
        "label": "Domicilio de actividades",
        "type": "text",
    },
    {"name": "telefono", "label": "Teléfono", "type": "text"},
    {"name": "celular", "label": "Celular", "type": "text"},
    {"name": "correo", "label": "Correo", "type": "text"},
    {"name": "sitio_web", "label": "Sitio web", "type": "text"},
    {"name": "link_redes", "label": "Link redes", "type": "text"},
    {
        "name": "nombre_referente",
        "label": "Nombre del referente",
        "type": "text",
    },
    {
        "name": "apellido_referente",
        "label": "Apellido del referente",
        "type": "text",
    },
    {
        "name": "telefono_referente",
        "label": "Teléfono del referente",
        "type": "text",
    },
    {
        "name": "correo_referente",
        "label": "Correo del referente",
        "type": "text",
    },
    {"name": "activo", "label": "Activo", "type": "boolean"},
]


def get_filters_ui_config() -> Dict[str, Any]:
    """Configuración serializable para el front de filtros avanzados."""

    return {
        "fields": FILTER_FIELDS,
        "operators": {
            "text": list(TEXT_OPS),
            "number": list(NUM_OPS),
            "boolean": list(BOOL_OPS),
        },
    }


__all__ = [
    "FIELD_MAP",
    "FIELD_TYPES",
    "TEXT_OPS",
    "NUM_OPS",
    "BOOL_OPS",
    "FILTER_FIELDS",
    "get_filters_ui_config",
]
