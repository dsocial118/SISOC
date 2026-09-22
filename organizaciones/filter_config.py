"""Configuracion de filtros combinables para el listado de Organizaciones.

Espeja `comedores/services/filter_config` para que el listado de organizaciones
y el selector de destinatarios de comunicados compartan exactamente los mismos
campos (issue #2505).
"""

from copy import deepcopy
from typing import Any, Dict

from django.core.cache import cache

from core.services.advanced_filters import AdvancedFilterEngine

# Mapea el nombre de campo expuesto en filtros -> lookup real en Django ORM
FIELD_MAP: Dict[str, str] = {
    # Texto simples
    "nombre": "nombre",
    "sigla": "sigla",
    "email": "email",
    "domicilio": "domicilio",
    "partido": "partido",
    # FKs -> nombre
    "tipo_entidad": "tipo_entidad__nombre",
    "subtipo_entidad": "subtipo_entidad__nombre",
    "provincia": "provincia__nombre",
    "municipio": "municipio__nombre",
    "localidad": "localidad__nombre",
    "codigo_de_proyecto": "proyectos__codigo",
    "comedor": "comedor__nombre",
    # Numericos
    "id": "id",
    "cuit": "cuit",
    "telefono": "telefono",
    # Booleanos
    "sin_vencimiento": "sin_vencimiento",
    # Fechas
    "fecha_vencimiento": "fecha_vencimiento",
    "fecha_creacion": "fecha_creacion",
}

FIELD_TYPES: Dict[str, str] = {
    **{
        k: "text"
        for k in [
            "nombre",
            "sigla",
            "email",
            "domicilio",
            "partido",
            "provincia",
            "municipio",
            "localidad",
            "codigo_de_proyecto",
            "comedor",
        ]
    },
    **{
        k: "choice"
        for k in [
            "tipo_entidad",
            "subtipo_entidad",
        ]
    },
    "sin_vencimiento": "boolean",
    **{
        k: "number"
        for k in [
            "id",
            "cuit",
            "telefono",
        ]
    },
    **{
        k: "date"
        for k in [
            "fecha_vencimiento",
            "fecha_creacion",
        ]
    },
}

# Operadores permitidos por tipo (mismos que comedores)
TEXT_OPS = ["contains", "ncontains", "eq", "ne", "empty"]
NUM_OPS = ["eq", "ne", "gt", "lt", "empty"]
CHOICE_OPS = ["eq", "ne"]
BOOL_OPS = ["eq", "ne"]
DATE_OPS = ["eq", "ne", "gt", "lt", "gte", "lte", "empty"]

FILTER_FIELDS = [
    {"name": "nombre", "label": "Nombre", "type": "text"},
    {"name": "sigla", "label": "Sigla", "type": "text"},
    {"name": "cuit", "label": "CUIT", "type": "number"},
    {"name": "telefono", "label": "Telefono", "type": "number"},
    {"name": "email", "label": "Email", "type": "text"},
    {"name": "tipo_entidad", "label": "Tipo de entidad", "type": "choice"},
    {"name": "subtipo_entidad", "label": "Subtipo de entidad", "type": "choice"},
    {"name": "domicilio", "label": "Domicilio", "type": "text"},
    {"name": "partido", "label": "Partido", "type": "text"},
    {"name": "provincia", "label": "Provincia (nombre)", "type": "text"},
    {"name": "municipio", "label": "Municipio (nombre)", "type": "text"},
    {"name": "localidad", "label": "Localidad (nombre)", "type": "text"},
    {"name": "comedor", "label": "Espacio comunitario (nombre)", "type": "text"},
    {
        "name": "codigo_de_proyecto",
        "label": "Codigo de proyecto",
        "type": "text",
    },
    {"name": "sin_vencimiento", "label": "Sin vencimiento?", "type": "boolean"},
    {
        "name": "fecha_vencimiento",
        "label": "Fecha de vencimiento",
        "type": "date",
    },
    {"name": "fecha_creacion", "label": "Fecha de creacion", "type": "date"},
    {"name": "id", "label": "ID", "type": "number"},
]

ORGANIZACION_ADVANCED_FILTER = AdvancedFilterEngine(
    field_map=FIELD_MAP,
    field_types=FIELD_TYPES,
    allowed_ops={
        "text": TEXT_OPS,
        "number": NUM_OPS,
        "choice": CHOICE_OPS,
        "boolean": BOOL_OPS,
        "date": DATE_OPS,
    },
)

DEFAULT_FIELD = "nombre"
FILTERS_UI_CONFIG_CACHE_KEY = "organizaciones:filters_ui_config:v1"
FILTERS_UI_CONFIG_CACHE_TTL = 60 * 15


def get_filters_ui_config() -> Dict[str, Any]:
    """Configuracion serializable para la UI de filtros avanzados."""

    cached_config = cache.get(FILTERS_UI_CONFIG_CACHE_KEY)
    if cached_config is not None:
        return deepcopy(cached_config)

    fields = [dict(field) for field in FILTER_FIELDS]

    try:
        from organizaciones.models import SubtipoEntidad, TipoEntidad

        def build_choices(queryset):
            return [
                {"value": nombre, "label": nombre}
                for nombre in queryset.order_by("nombre")
                .values_list("nombre", flat=True)
                .distinct()
                if nombre
            ]

        choices_by_field = {
            "tipo_entidad": build_choices(TipoEntidad.objects),
            "subtipo_entidad": build_choices(
                SubtipoEntidad.objects.filter(activo=True)
            ),
        }

        for field in fields:
            name = field.get("name")
            if name in choices_by_field and choices_by_field[name]:
                field["choices"] = choices_by_field[name]
    except Exception:
        # Si no hay tablas (migraciones pendientes) se devuelven los campos base.
        pass

    config = {
        "fields": fields,
        "defaultField": DEFAULT_FIELD,
        "operators": {
            "text": list(TEXT_OPS),
            "number": list(NUM_OPS),
            "choice": list(CHOICE_OPS),
            "boolean": list(BOOL_OPS),
            "date": list(DATE_OPS),
        },
    }
    cache.set(FILTERS_UI_CONFIG_CACHE_KEY, config, FILTERS_UI_CONFIG_CACHE_TTL)
    return deepcopy(config)


__all__ = [
    "ORGANIZACION_ADVANCED_FILTER",
    "FIELD_MAP",
    "FIELD_TYPES",
    "TEXT_OPS",
    "NUM_OPS",
    "CHOICE_OPS",
    "BOOL_OPS",
    "DATE_OPS",
    "FILTER_FIELDS",
    "DEFAULT_FIELD",
    "get_filters_ui_config",
]
