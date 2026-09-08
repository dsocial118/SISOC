"""Reglas de visibilidad de navegación propias de CDI."""

from typing import Any

from centrodeinfancia.access import GRUPOS_CDI_LOCALES
from core.constants import UserGroups
from core.services.sidebar_access import registrar_predicado_sidebar


GRUPOS_SIMEPI = frozenset(
    (
        UserGroups.SIMEPI_ADMINISTRADOR,
        UserGroups.SIMEPI_ANALISTA_DATOS,
        UserGroups.SIMEPI_EQUIPO_NACIONAL,
        UserGroups.SIMEPI_AUDITORIA,
        UserGroups.SIMEPI_EGP,
    )
)


def es_usuario_solo_cdi_local(user: Any) -> bool:
    """Oculta Comunicados sólo a roles CDI locales sin rol SIMEPI adicional."""
    if not user or not getattr(user, "is_authenticated", False) or user.is_superuser:
        return False
    group_names = set(user.groups.values_list("name", flat=True))
    return bool(group_names & GRUPOS_CDI_LOCALES) and not bool(
        group_names & GRUPOS_SIMEPI
    )


def registrar_acceso_sidebar() -> None:
    registrar_predicado_sidebar("cdi_local", es_usuario_solo_cdi_local)
