"""Contribuciones de filtros favoritos de Usuarios."""

from core.services.favorite_filters import (
    ConfiguracionFiltrosSeccion,
    SeccionesFiltrosFavoritos,
    registrar_configuracion_seccion,
)
from users.users_filter_config import FIELD_TYPES, NUM_OPS, TEXT_OPS


def registrar_filtros_favoritos() -> None:
    registrar_configuracion_seccion(
        SeccionesFiltrosFavoritos.USUARIOS,
        ConfiguracionFiltrosSeccion(
            tipos_campos=FIELD_TYPES,
            operadores_permitidos={"text": TEXT_OPS, "number": NUM_OPS},
        ),
    )
