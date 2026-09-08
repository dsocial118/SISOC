"""Contribucion de filtros favoritos de Acompanamientos."""

from acompanamientos.services.filter_config import (
    CHOICE_OPS,
    DATE_OPS,
    FIELD_TYPES,
    NUM_OPS,
    TEXT_OPS,
)
from core.services.favorite_filters import (
    ConfiguracionFiltrosSeccion,
    SeccionesFiltrosFavoritos,
    registrar_configuracion_seccion,
)


def registrar_filtros_favoritos() -> None:
    registrar_configuracion_seccion(
        SeccionesFiltrosFavoritos.ACOMPANAMIENTOS,
        ConfiguracionFiltrosSeccion(
            tipos_campos=FIELD_TYPES,
            operadores_permitidos={
                "text": TEXT_OPS,
                "number": NUM_OPS,
                "date": DATE_OPS,
                "choice": CHOICE_OPS,
            },
        ),
    )
