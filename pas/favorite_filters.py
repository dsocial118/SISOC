"""Contribución pública de PAS al registro de filtros favoritos."""

from core.services.favorite_filters import (
    ConfiguracionFiltrosSeccion,
    registrar_configuracion_seccion,
)
from pas.services.filter_config import (
    CHOICE_OPS,
    FIELD_TYPES,
    NUM_OPS,
    TEXT_OPS,
)


PAS_FILTER_SECTION = "pas"


def registrar_filtros_favoritos() -> None:
    registrar_configuracion_seccion(
        PAS_FILTER_SECTION,
        ConfiguracionFiltrosSeccion(
            tipos_campos=FIELD_TYPES,
            operadores_permitidos={
                "text": TEXT_OPS,
                "number": NUM_OPS,
                "choice": CHOICE_OPS,
            },
        ),
    )
