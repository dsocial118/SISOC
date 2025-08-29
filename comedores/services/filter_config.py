"""Configuración de filtros combinables para ComedorService.

Centraliza mapeos de campos, tipos y operadores permitidos para
evitar duplicación y facilitar mantenimiento.
"""
from typing import Dict

# Mapea el nombre de campo expuesto en filtros -> lookup real en Django ORM
FIELD_MAP: Dict[str, str] = {
    # Texto simples
    "nombre": "nombre",
    "estado": "estado",
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
    **{k: "text" for k in [
        "nombre",
        "estado",
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
    ]},
    # Numéricos
    **{k: "number" for k in [
        "id",
        "id_externo",
        "comienzo",
        "numero",
        "codigo_postal",
        "latitud",
        "longitud",
    ]},
}

# Operadores permitidos por tipo
TEXT_OPS = {"eq", "ne", "contains", "ncontains", "empty"}
NUM_OPS = {"eq", "ne", "gt", "lt", "empty"}

