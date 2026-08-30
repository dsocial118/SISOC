"""Adaptadores temporales a los filtros compartidos del monolito."""

from core.services.advanced_filters import AdvancedFilterEngine
from core.services.favorite_filters import (
    ConfiguracionFiltrosSeccion,
    SeccionesFiltrosFavoritos,
    registrar_configuracion_seccion,
)

from services.dispositivos.monolith_compat.app.dispositivos_filter_config import (
    CHOICE_OPS,
    FIELD_MAP,
    FIELD_TYPES,
    NUM_OPS,
    TEXT_OPS,
)


_advanced_filter = AdvancedFilterEngine(
    field_map=FIELD_MAP,
    field_types=FIELD_TYPES,
    allowed_ops={
        "text": TEXT_OPS,
        "number": NUM_OPS,
        "choice": CHOICE_OPS,
    },
)


def aplicar_filtros_avanzados(queryset, request):
    return _advanced_filter.filter_queryset(queryset, request)


def seccion_filtros_favoritos():
    return SeccionesFiltrosFavoritos.DISPOSITIVOS


def registrar_filtros_favoritos() -> None:
    registrar_configuracion_seccion(
        SeccionesFiltrosFavoritos.DISPOSITIVOS,
        ConfiguracionFiltrosSeccion(
            tipos_campos=FIELD_TYPES,
            operadores_permitidos={
                "text": TEXT_OPS,
                "number": NUM_OPS,
                "choice": CHOICE_OPS,
            },
        ),
    )
