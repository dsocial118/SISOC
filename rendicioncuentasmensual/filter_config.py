"""Configuracion de filtros combinables para Rendiciones."""

from copy import deepcopy
from typing import Any, Dict

from django.core.cache import cache

from rendicioncuentasmensual.models import RendicionCuentaMensual

FIELD_MAP: Dict[str, str] = {
    "codigo_proyecto": "comedor__codigo_de_proyecto",
    "comedor": "comedor__nombre",
    "organizacion": "comedor__organizacion__nombre",
    "convenio": "convenio",
    "numero_rendicion": "numero_rendicion",
    "mes": "mes",
    "anio": "anio",
    "periodo_inicio": "periodo_inicio",
    "periodo_fin": "periodo_fin",
    "linea_programatica": "linea_programatica",
    "estado": "estado",
    "etapa_proceso": "etapa_proceso",
    "documento_adjunto": "documento_adjunto",
    "fecha_creacion": "fecha_creacion__date",
    "ultima_modificacion": "ultima_modificacion__date",
}

FIELD_TYPES: Dict[str, str] = {
    "codigo_proyecto": "text",
    "comedor": "text",
    "organizacion": "text",
    "convenio": "text",
    "numero_rendicion": "number",
    "mes": "number",
    "anio": "number",
    "periodo_inicio": "date",
    "periodo_fin": "date",
    "linea_programatica": "choice",
    "estado": "choice",
    "etapa_proceso": "choice",
    "documento_adjunto": "boolean",
    "fecha_creacion": "date",
    "ultima_modificacion": "date",
}

TEXT_OPS = ["contains", "ncontains", "eq", "ne", "empty"]
NUM_OPS = ["eq", "ne", "gt", "lt", "empty"]
DATE_OPS = ["eq", "ne", "gt", "lt", "empty"]
CHOICE_OPS = ["eq", "ne"]
BOOL_OPS = ["eq", "ne"]

LINEA_PROGRAMATICA_CHOICES = list(RendicionCuentaMensual.LINEA_PROGRAMATICA_CHOICES)

ESTADO_CHOICES = list(RendicionCuentaMensual.ESTADO_CHOICES)

# El valor combina los dos campos que construyen ``estado_proceso_display``.
# Se exponen solamente las combinaciones alcanzables por el flujo de negocio.
ESTADO_PROCESO_CHOICES = [
    ("carga_documentacion:en_curso", "Carga de documentación en curso"),
    ("revision_documentacion:pendiente", "Revisión Territorial pendiente"),
    ("revision_documentacion:en_curso", "Revisión Territorial en curso"),
    (
        "revision_documentacion:pendiente_correcciones",
        "Revisión Territorial pendiente de correcciones",
    ),
    ("revision_documentacion:subsanado", "Revisión Territorial subsanado"),
    ("revision_auditoria:pendiente", "Revisión de Auditoría pendiente"),
    ("revision_auditoria:en_curso", "Revisión de Auditoría en curso"),
    (
        "revision_auditoria:pendiente_correcciones",
        "Revisión de Auditoría pendiente de correcciones",
    ),
    ("revision_auditoria:subsanado", "Revisión de Auditoría subsanado"),
    ("auditoria:pendiente", "Auditoría pendiente"),
    ("auditoria:en_curso", "Auditoría en curso"),
    ("auditoria:finalizada", "Auditoría finalizada sin observaciones"),
    (
        "auditoria:finalizada_con_observaciones",
        "Auditoría finalizada con observaciones",
    ),
    ("regularizacion:en_curso", "Regularización en curso"),
    ("regularizacion:finalizada", "Rendición regularizada tras Auditoría"),
]
ETAPA_CHOICES = list(RendicionCuentaMensual.ETAPA_PROCESO_CHOICES)

FILTER_FIELDS = [
    {"name": "codigo_proyecto", "label": "Proyecto", "type": "text"},
    {"name": "comedor", "label": "Espacio", "type": "text"},
    {"name": "organizacion", "label": "Organizacion", "type": "text"},
    {"name": "convenio", "label": "Convenio", "type": "text"},
    {"name": "numero_rendicion", "label": "Numero de rendicion", "type": "number"},
    {
        "name": "mes",
        "label": "Mes",
        "type": "number",
        "input": {"min": "1", "max": "12"},
    },
    {"name": "anio", "label": "Anio", "type": "number"},
    {"name": "periodo_inicio", "label": "Periodo inicio", "type": "date"},
    {"name": "periodo_fin", "label": "Periodo fin", "type": "date"},
    {
        "name": "linea_programatica",
        "label": "Linea programatica",
        "type": "choice",
        "choices": [
            {"value": value, "label": label}
            for value, label in LINEA_PROGRAMATICA_CHOICES
        ],
    },
    {
        "name": "estado_proceso",
        "label": "Estado",
        "type": "choice",
        "choices": [
            {"value": value, "label": label} for value, label in ESTADO_PROCESO_CHOICES
        ],
    },
    {
        "name": "estado",
        "label": "Estado general",
        "type": "choice",
        "choices": [
            {"value": value, "label": label} for value, label in ESTADO_CHOICES
        ],
    },
    {
        "name": "etapa_proceso",
        "label": "Etapa",
        "type": "choice",
        "choices": [{"value": value, "label": label} for value, label in ETAPA_CHOICES],
    },
    {"name": "documento_adjunto", "label": "Documento adjunto", "type": "boolean"},
    {"name": "fecha_creacion", "label": "Fecha de creacion", "type": "date"},
    {"name": "ultima_modificacion", "label": "Ultima modificacion", "type": "date"},
]

DEFAULT_FIELD = "codigo_proyecto"
FILTERS_UI_CONFIG_CACHE_KEY = "rendiciones:filters_ui_config:v3"
FILTERS_UI_CONFIG_CACHE_TTL = 60 * 15


def get_filters_ui_config() -> Dict[str, Any]:
    cached_config = cache.get(FILTERS_UI_CONFIG_CACHE_KEY)
    if cached_config is not None:
        return deepcopy(cached_config)

    config = {
        "fields": [dict(field) for field in FILTER_FIELDS],
        "operators": {
            "text": list(TEXT_OPS),
            "number": list(NUM_OPS),
            "date": list(DATE_OPS),
            "choice": list(CHOICE_OPS),
            "boolean": list(BOOL_OPS),
        },
    }
    cache.set(FILTERS_UI_CONFIG_CACHE_KEY, config, FILTERS_UI_CONFIG_CACHE_TTL)
    return deepcopy(config)


__all__ = [
    "FIELD_MAP",
    "FIELD_TYPES",
    "TEXT_OPS",
    "NUM_OPS",
    "DATE_OPS",
    "CHOICE_OPS",
    "BOOL_OPS",
    "FILTER_FIELDS",
    "DEFAULT_FIELD",
    "get_filters_ui_config",
]
