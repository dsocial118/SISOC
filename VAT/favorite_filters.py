"""Contribuciones de filtros favoritos de VAT."""

from VAT.services.centro_filter_config import (
    BOOL_OPS,
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
        SeccionesFiltrosFavoritos.VAT_CENTROS,
        ConfiguracionFiltrosSeccion(
            tipos_campos=FIELD_TYPES,
            operadores_permitidos={
                "text": TEXT_OPS,
                "number": NUM_OPS,
                "boolean": BOOL_OPS,
            },
        ),
    )
