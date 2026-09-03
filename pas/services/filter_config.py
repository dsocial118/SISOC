from copy import deepcopy

from django.core.cache import cache

from pas.models import PasAviso, PasEstado

FIELD_MAP = {
    "id_persona": "id_persona",
    "nombre": "nombres",
    "apellido": "apellidos",
    "dni": "dni",
    "provincia": "provincia__nombre",
    "estado": "estado__nombre",
    "aviso": "avisos__descripcion",
}

FIELD_TYPES = {
    "id_persona": "number",
    "nombre": "text",
    "apellido": "text",
    "dni": "number",
    "provincia": "text",
    "estado": "choice",
    "aviso": "choice",
}

TEXT_OPS = ["contains", "ncontains", "eq", "ne", "empty"]
NUM_OPS = ["eq", "ne", "gt", "lt", "empty"]
CHOICE_OPS = ["eq", "ne"]

FILTER_FIELDS = [
    {"name": "nombre", "label": "Nombre", "type": "text"},
    {"name": "apellido", "label": "Apellido", "type": "text"},
    {"name": "dni", "label": "DNI", "type": "number"},
    {"name": "provincia", "label": "Provincia", "type": "text"},
    {"name": "estado", "label": "Estado", "type": "choice"},
    {"name": "aviso", "label": "Aviso", "type": "choice"},
]

FILTERS_UI_CONFIG_CACHE_KEY = "pas:filters_ui_config:v1"
FILTERS_UI_CONFIG_CACHE_TTL = 60 * 15


def get_filters_ui_config():
    cached_config = cache.get(FILTERS_UI_CONFIG_CACHE_KEY)
    if cached_config is not None:
        return deepcopy(cached_config)

    fields = [dict(field) for field in FILTER_FIELDS]
    choices_by_field = {
        "estado": [
            {"value": nombre, "label": nombre}
            for nombre in PasEstado.objects.order_by("nombre").values_list(
                "nombre", flat=True
            )
        ],
        "aviso": [
            {"value": descripcion, "label": descripcion}
            for descripcion in PasAviso.objects.order_by("codigo").values_list(
                "descripcion", flat=True
            )
        ],
    }
    for field in fields:
        choices = choices_by_field.get(field["name"])
        if choices:
            field["choices"] = choices

    config = {
        "fields": fields,
        "operators": {
            "text": list(TEXT_OPS),
            "number": list(NUM_OPS),
            "choice": list(CHOICE_OPS),
        },
    }
    cache.set(FILTERS_UI_CONFIG_CACHE_KEY, config, FILTERS_UI_CONFIG_CACHE_TTL)
    return deepcopy(config)
