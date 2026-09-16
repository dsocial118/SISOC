"""Regla de navegación exclusiva del dominio DataCalle (QA-0014)."""

from typing import Any

from core.services.sidebar_access import registrar_predicado_sidebar
from users.services_datacalle import es_coordinador_calle


def es_usuario_solo_datacalle(user: Any) -> bool:
    """Indica si el menú debe mostrar sólo lo de Situación de Calle.

    Es el coordinador provincial que entra al backoffice únicamente a
    planificar operativos y mirar casos: el resto de los módulos (comedores,
    vouchers, programas) no le sirven y le agregan ruido.

    Un usuario con otros permisos del sistema no entra acá: se detecta por
    tener permisos de DataCalle **y no** los de comedores, que es el dominio
    grande del backoffice.
    """
    if not user or not user.is_authenticated or user.is_superuser:
        return False
    if not es_coordinador_calle(user):
        return False
    return not user.has_perm("comedores.view_comedor")


def registrar_acceso_sidebar() -> None:
    registrar_predicado_sidebar("datacalle", es_usuario_solo_datacalle)
