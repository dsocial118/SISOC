"""Contribuciones de filtros favoritos de Dispositivos."""

from core.services.favorite_filters import (
    ConfiguracionFiltrosSeccion,
    SeccionesFiltrosFavoritos,
    registrar_configuracion_seccion,
)
from dispositivos.dispositivos_filter_config import (
    CHOICE_OPS,
    FIELD_TYPES,
    NUM_OPS,
    TEXT_OPS,
)


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
