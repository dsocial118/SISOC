"""Configuración de filtros combinables para ComedorService.

Centraliza mapeos de campos, tipos y operadores permitidos para
evitar duplicación y facilitar mantenimiento.
"""

from typing import Any, Dict

# Mapea el nombre de campo expuesto en filtros -> lookup real en Django ORM
FIELD_MAP: Dict[str, str] = {
    # Texto simples
    "nombre": "nombre",
    "estado": "estado",
    "estado_general": "estado_general",
    "calle": "calle",
    "piso": "piso",
    "departamento": "departamento",
    "manzana": "manzana",
    "lote": "lote",
    "entre_calle_1": "entre_calle_1",
    "entre_calle_2": "entre_calle_2",
    "partido": "partido",
    "barrio": "barrio",
    "codigo_de_proyecto": "codigo_de_proyecto",
    # FKs -> nombre
    "organizacion": "organizacion__nombre",
    "programa": "programa__nombre",
    "tipocomedor": "tipocomedor__nombre",
    "dupla": "dupla__nombre",
    "provincia": "provincia__nombre",
    "municipio": "municipio__nombre",
    "localidad": "localidad__nombre",
    "referente": "referente__nombre",
    # Numéricos
    "id": "id",
    "id_externo": "id_externo",
    "comienzo": "comienzo",
    "numero": "numero",
    "codigo_postal": "codigo_postal",
    "latitud": "latitud",
    "longitud": "longitud",
}

# Tipos: text | number (utilizados para validación y casteo)
FIELD_TYPES: Dict[str, str] = {
    # Texto
    **{
        k: "text"
        for k in [
            "nombre",
            "estado",
            "estado_general",
            "calle",
            "piso",
            "departamento",
            "manzana",
            "lote",
            "entre_calle_1",
            "entre_calle_2",
            "partido",
            "barrio",
            "organizacion",
            "programa",
            "tipocomedor",
            "dupla",
            "provincia",
            "municipio",
            "localidad",
            "referente",
            "codigo_de_proyecto",
        ]
    },
    # Numéricos
    **{
        k: "number"
        for k in [
            "id",
            "id_externo",
            "comienzo",
            "numero",
            "codigo_postal",
            "latitud",
            "longitud",
        ]
    },
}

# Operadores permitidos por tipo
TEXT_OPS = ["contains", "ncontains", "eq", "ne", "empty"]
NUM_OPS = ["eq", "ne", "gt", "lt", "empty"]

# Configuración para la UI de filtros avanzados
FILTER_FIELDS = [
    {"name": "nombre", "label": "Nombre", "type": "text"},
    {"name": "estado", "label": "Estado", "type": "text"},
    {"name": "estado_general", "label": "Estado general", "type": "text"},
    {"name": "calle", "label": "Calle", "type": "text"},
    {"name": "piso", "label": "Piso", "type": "text"},
    {"name": "departamento", "label": "Departamento", "type": "text"},
    {"name": "manzana", "label": "Manzana", "type": "text"},
    {"name": "lote", "label": "Lote", "type": "text"},
    {"name": "entre_calle_1", "label": "Entre calle 1", "type": "text"},
    {"name": "entre_calle_2", "label": "Entre calle 2", "type": "text"},
    {"name": "partido", "label": "Partido", "type": "text"},
    {"name": "barrio", "label": "Barrio", "type": "text"},
    {"name": "organizacion", "label": "Organización (nombre)", "type": "text"},
    {"name": "programa", "label": "Programa (nombre)", "type": "text"},
    {"name": "tipocomedor", "label": "Tipo de comedor (nombre)", "type": "text"},
    {"name": "dupla", "label": "Dupla (nombre)", "type": "text"},
    {"name": "provincia", "label": "Provincia (nombre)", "type": "text"},
    {"name": "municipio", "label": "Municipio (nombre)", "type": "text"},
    {"name": "localidad", "label": "Localidad (nombre)", "type": "text"},
    {"name": "referente", "label": "Referente (nombre)", "type": "text"},
    {
        "name": "codigo_de_proyecto",
        "label": "Código de proyecto",
        "type": "text",
    },
    {"name": "id", "label": "ID", "type": "number"},
    {"name": "id_externo", "label": "ID Externo", "type": "number"},
    {"name": "comienzo", "label": "Comienzo (año)", "type": "number"},
    {"name": "numero", "label": "Número", "type": "number"},
    {"name": "codigo_postal", "label": "Código Postal", "type": "number"},
    {
        "name": "latitud",
        "label": "Latitud",
        "type": "number",
        "input": {"step": "any"},
    },
    {
        "name": "longitud",
        "label": "Longitud",
        "type": "number",
        "input": {"step": "any"},
    },
]

DEFAULT_FIELD = "nombre"


def get_filters_ui_config() -> Dict[str, Any]:
    """Configuración serializable para la UI de filtros avanzados."""

    return {
        "fields": FILTER_FIELDS,
        "operators": {
            "text": list(TEXT_OPS),
            "number": list(NUM_OPS),
        },
    }


__all__ = [
    "FIELD_MAP",
    "FIELD_TYPES",
    "TEXT_OPS",
    "NUM_OPS",
    "FILTER_FIELDS",
    "DEFAULT_FIELD",
    "get_filters_ui_config",
]
