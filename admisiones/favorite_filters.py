"""Contribuciones de filtros favoritos de Admisiones."""

from admisiones.services.admisiones_filter_config import (  # pylint: disable=no-name-in-module
    CHOICE_OPS as TECNICOS_OPS_ELECCION,
    DATE_OPS as TECNICOS_OPS_FECHA,
    FIELD_TYPES as TECNICOS_TIPOS_CAMPOS,
    NUM_OPS as TECNICOS_OPS_NUMERO,
    TEXT_OPS as TECNICOS_OPS_TEXTO,
)
from admisiones.services.legales_filter_config import (  # pylint: disable=no-name-in-module
    CHOICE_OPS as LEGALES_OPS_ELECCION,
    DATE_OPS as LEGALES_OPS_FECHA,
    FIELD_TYPES as LEGALES_TIPOS_CAMPOS,
    NUM_OPS as LEGALES_OPS_NUMERO,
    TEXT_OPS as LEGALES_OPS_TEXTO,
)
from core.services.favorite_filters import (
    ConfiguracionFiltrosSeccion,
    SeccionesFiltrosFavoritos,
    registrar_configuracion_seccion,
)


def registrar_filtros_favoritos() -> None:
    registrar_configuracion_seccion(
        SeccionesFiltrosFavoritos.ADMISIONES_TECNICOS,
        ConfiguracionFiltrosSeccion(
            tipos_campos=TECNICOS_TIPOS_CAMPOS,
            operadores_permitidos={
                "text": TECNICOS_OPS_TEXTO,
                "number": TECNICOS_OPS_NUMERO,
                "date": TECNICOS_OPS_FECHA,
                "choice": TECNICOS_OPS_ELECCION,
            },
        ),
    )
    registrar_configuracion_seccion(
        SeccionesFiltrosFavoritos.ADMISIONES_LEGALES,
        ConfiguracionFiltrosSeccion(
            tipos_campos=LEGALES_TIPOS_CAMPOS,
            operadores_permitidos={
                "text": LEGALES_OPS_TEXTO,
                "number": LEGALES_OPS_NUMERO,
                "date": LEGALES_OPS_FECHA,
                "choice": LEGALES_OPS_ELECCION,
            },
        ),
    )
