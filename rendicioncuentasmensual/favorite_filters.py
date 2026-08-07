"""Contribuciones de filtros favoritos de Rendiciones Mensuales."""

from core.services.favorite_filters import (
    ConfiguracionFiltrosSeccion,
    SeccionesFiltrosFavoritos,
    registrar_configuracion_seccion,
)
from rendicioncuentasmensual.filter_config import (
    BOOL_OPS,
    CHOICE_OPS,
    DATE_OPS,
    FIELD_TYPES,
    NUM_OPS,
    TEXT_OPS,
)


def registrar_filtros_favoritos() -> None:
    registrar_configuracion_seccion(
        SeccionesFiltrosFavoritos.RENDICIONES,
        ConfiguracionFiltrosSeccion(
            tipos_campos=FIELD_TYPES,
            operadores_permitidos={
                "text": TEXT_OPS,
                "number": NUM_OPS,
                "date": DATE_OPS,
                "choice": CHOICE_OPS,
                "boolean": BOOL_OPS,
            },
        ),
    )
