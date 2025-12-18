"""Configuración de filtros combinables para ComedorService.

Centraliza mapeos de campos, tipos y operadores permitidos para evitar
duplicación y facilitar mantenimiento.
"""

from typing import Any, Dict

# Mapea el nombre de campo expuesto en filtros -> lookup real en Django ORM
FIELD_MAP: Dict[str, str] = {
    # Texto simples
    "nombre": "nombre",
    "estado": "estado",
    "estado_general": "ultimo_estado__estado_general__estado_actividad__estado",
    "estado_actividad": "ultimo_estado__estado_general__estado_actividad__estado",
    "estado_proceso": "ultimo_estado__estado_general__estado_proceso__estado",
    "estado_detalle": "ultimo_estado__estado_general__estado_detalle__estado",
    "estado_validacion": "estado_validacion",
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
    "referente_apellido": "referente__apellido",
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
            "referente_apellido",
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
    # Elecciones
    **{
        k: "choice"
        for k in [
            "estado_actividad",
            "estado_proceso",
            "estado_detalle",
            "estado_validacion",
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
CHOICE_OPS = ["eq", "ne"]

# Configuración para la UI de filtros avanzados
FILTER_FIELDS = [
    {"name": "nombre", "label": "Nombre", "type": "text"},
    {"name": "estado", "label": "Estado", "type": "text"},
    {"name": "estado_general", "label": "Estado general", "type": "text"},
    {"name": "estado_actividad", "label": "Estado de actividad", "type": "choice"},
    {"name": "estado_proceso", "label": "Estado de proceso", "type": "choice"},
    {"name": "estado_detalle", "label": "Estado de detalle", "type": "choice"},
    {"name": "estado_validacion", "label": "Estado de validación", "type": "choice"},
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
    {"name": "referente_apellido", "label": "Referente (apellido)", "type": "text"},
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

    fields = [dict(field) for field in FILTER_FIELDS]

    try:
        from comedores.models import (
            Comedor,
            EstadoActividad,
            EstadoProceso,
            EstadoDetalle,
        )

        def build_state_choices(model_cls):
            return [
                {"value": value, "label": value}
                for value in model_cls.objects.order_by("estado")
                .values_list("estado", flat=True)
                .distinct()
                if value
            ]

        choices_by_field = {
            "estado_actividad": build_state_choices(EstadoActividad),
            "estado_proceso": build_state_choices(EstadoProceso),
            "estado_detalle": build_state_choices(EstadoDetalle),
            "estado_validacion": [
                {"value": value, "label": label}
                for value, label in Comedor.ESTADOS_VALIDACION
            ],
        }

        for field in fields:
            name = field.get("name")
            if name in choices_by_field and choices_by_field[name]:
                field["choices"] = choices_by_field[name]
    except Exception:
        # Si no hay tablas (migraciones pendientes) se devuelven los campos base sin choices
        pass

    return {
        "fields": fields,
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
    "DEFAULT_FIELD",
    "get_filters_ui_config",
]
