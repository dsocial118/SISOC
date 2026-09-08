"""Contribuciones de filtros favoritos de Comedores."""

from comedores.services.filter_config import (  # pylint: disable=no-name-in-module
    BOOL_OPS,
    CHOICE_OPS,
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
        SeccionesFiltrosFavoritos.COMEDORES,
        ConfiguracionFiltrosSeccion(
            tipos_campos=FIELD_TYPES,
            operadores_permitidos={
                "text": TEXT_OPS,
                "number": NUM_OPS,
                "choice": CHOICE_OPS,
                "boolean": BOOL_OPS,
            },
        ),
    )
