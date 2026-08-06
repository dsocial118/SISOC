"""Contribuciones de filtros favoritos de Centro de Familia."""

from centrodefamilia.services.beneficiarios_filter_config import (
    CHOICE_OPS as BENEFICIARIOS_OPS_ELECCION,
    FIELD_TYPES as BENEFICIARIOS_TIPOS_CAMPOS,
    NUM_OPS as BENEFICIARIOS_OPS_NUMERO,
    TEXT_OPS as BENEFICIARIOS_OPS_TEXTO,
)
from centrodefamilia.services.centro_filter_config import (
    BOOL_OPS as CENTROS_OPS_BOOLEANO,
    FIELD_TYPES as CENTROS_TIPOS_CAMPOS,
    NUM_OPS as CENTROS_OPS_NUMERO,
    TEXT_OPS as CENTROS_OPS_TEXTO,
)
from centrodefamilia.services.responsables_filter_config import (
    CHOICE_OPS as RESPONSABLES_OPS_ELECCION,
    FIELD_TYPES as RESPONSABLES_TIPOS_CAMPOS,
    NUM_OPS as RESPONSABLES_OPS_NUMERO,
    TEXT_OPS as RESPONSABLES_OPS_TEXTO,
)
from core.services.favorite_filters import (
    ConfiguracionFiltrosSeccion,
    SeccionesFiltrosFavoritos,
    registrar_configuracion_seccion,
)


def registrar_filtros_favoritos() -> None:
    registrar_configuracion_seccion(
        SeccionesFiltrosFavoritos.CDF_CENTROS,
        ConfiguracionFiltrosSeccion(
            tipos_campos=CENTROS_TIPOS_CAMPOS,
            operadores_permitidos={
                "text": CENTROS_OPS_TEXTO,
                "number": CENTROS_OPS_NUMERO,
                "boolean": CENTROS_OPS_BOOLEANO,
            },
        ),
    )
    registrar_configuracion_seccion(
        SeccionesFiltrosFavoritos.CDF_BENEFICIARIOS,
        ConfiguracionFiltrosSeccion(
            tipos_campos=BENEFICIARIOS_TIPOS_CAMPOS,
            operadores_permitidos={
                "text": BENEFICIARIOS_OPS_TEXTO,
                "number": BENEFICIARIOS_OPS_NUMERO,
                "choice": BENEFICIARIOS_OPS_ELECCION,
            },
        ),
    )
    registrar_configuracion_seccion(
        SeccionesFiltrosFavoritos.CDF_RESPONSABLES,
        ConfiguracionFiltrosSeccion(
            tipos_campos=RESPONSABLES_TIPOS_CAMPOS,
            operadores_permitidos={
                "text": RESPONSABLES_OPS_TEXTO,
                "number": RESPONSABLES_OPS_NUMERO,
                "choice": RESPONSABLES_OPS_ELECCION,
            },
        ),
    )
