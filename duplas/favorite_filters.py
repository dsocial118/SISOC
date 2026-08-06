"""Contribuciones de filtros favoritos de Duplas."""

from core.services.favorite_filters import (
    ConfiguracionFiltrosSeccion,
    SeccionesFiltrosFavoritos,
    registrar_configuracion_seccion,
)
from duplas.dupla_filter_config import FIELD_TYPES, NUM_OPS, TEXT_OPS


def registrar_filtros_favoritos() -> None:
    registrar_configuracion_seccion(
        SeccionesFiltrosFavoritos.DUPLAS,
        ConfiguracionFiltrosSeccion(
            tipos_campos=FIELD_TYPES,
            operadores_permitidos={"text": TEXT_OPS, "number": NUM_OPS},
        ),
    )
