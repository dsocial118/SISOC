"""
Módulo centralizado para validaciones de permisos en comunicados.
"""

from django.core.exceptions import PermissionDenied
from core.constants import UserGroups
from users.services import UserPermissionService


def _in_group(user, name: str) -> bool:
    """Verifica si el usuario pertenece a un grupo específico."""
    return user.is_authenticated and user.groups.filter(name=name).exists()


def is_admin(user) -> bool:
    """Verifica si el usuario es administrador."""
    return user.is_superuser or _in_group(user, UserGroups.ADMINISTRADOR)


def can_create_comunicado(user) -> bool:
    """Verifica si el usuario puede crear comunicados."""
    if not user.is_authenticated:
        return False
    return is_admin(user) or _in_group(user, UserGroups.COMUNICADO_CREAR)


def can_edit_comunicado(user, comunicado=None) -> bool:
    """
    Verifica si el usuario puede editar un comunicado.
    Solo se pueden editar borradores (excepto admins).
    """
    if not user.is_authenticated:
        return False

    if is_admin(user):
        return True

    if not _in_group(user, UserGroups.COMUNICADO_EDITAR):
        return False

    # Solo se pueden editar borradores
    if comunicado and comunicado.estado != "borrador":
        return False

    return True


def can_publish_comunicado(user) -> bool:
    """Verifica si el usuario puede publicar comunicados."""
    if not user.is_authenticated:
        return False
    return is_admin(user) or _in_group(user, UserGroups.COMUNICADO_PUBLICAR)


def can_archive_comunicado(user) -> bool:
    """Verifica si el usuario puede archivar comunicados."""
    if not user.is_authenticated:
        return False
    return is_admin(user) or _in_group(user, UserGroups.COMUNICADO_ARCHIVAR)


def can_delete_comunicado(user, comunicado=None) -> bool:
    """
    Verifica si el usuario puede eliminar un comunicado.
    Solo admins pueden eliminar, y solo borradores.
    """
    if not user.is_authenticated:
        return False

    if not is_admin(user):
        return False

    # Solo se pueden eliminar borradores
    if comunicado and comunicado.estado != "borrador":
        return False

    return True


def can_manage_comunicados(user) -> bool:
    """
    Verifica si el usuario tiene algún permiso de gestión de comunicados.
    Usado para mostrar/ocultar elementos de UI.
    """
    if not user.is_authenticated:
        return False

    return (
        is_admin(user)
        or _in_group(user, UserGroups.COMUNICADO_CREAR)
        or _in_group(user, UserGroups.COMUNICADO_EDITAR)
        or _in_group(user, UserGroups.COMUNICADO_PUBLICAR)
        or _in_group(user, UserGroups.COMUNICADO_ARCHIVAR)
    )


def require_create_permission(user):
    """Decorator helper: lanza PermissionDenied si no puede crear."""
    if not can_create_comunicado(user):
        raise PermissionDenied("No tiene permisos para crear comunicados.")


def require_edit_permission(user, comunicado=None):
    """Decorator helper: lanza PermissionDenied si no puede editar."""
    if not can_edit_comunicado(user, comunicado):
        raise PermissionDenied("No tiene permisos para editar este comunicado.")


def require_publish_permission(user):
    """Decorator helper: lanza PermissionDenied si no puede publicar."""
    if not can_publish_comunicado(user):
        raise PermissionDenied("No tiene permisos para publicar comunicados.")


def require_archive_permission(user):
    """Decorator helper: lanza PermissionDenied si no puede archivar."""
    if not can_archive_comunicado(user):
        raise PermissionDenied("No tiene permisos para archivar comunicados.")


def can_toggle_destacado(user) -> bool:
    """
    Verifica si el usuario puede cambiar el estado destacado de un comunicado.
    Admin y usuarios con permiso de publicar pueden hacerlo.
    """
    if not user.is_authenticated:
        return False
    return is_admin(user) or _in_group(user, UserGroups.COMUNICADO_PUBLICAR)


def require_toggle_destacado_permission(user):
    """Decorator helper: lanza PermissionDenied si no puede toggle destacado."""
    if not can_toggle_destacado(user):
        raise PermissionDenied("No tiene permisos para modificar el estado destacado.")


# =============================================================================
# PERMISOS V2 - Comunicados Internos y Externos (Comedores)
# =============================================================================

def es_tecnico(user) -> bool:
    """Verifica si el usuario es técnico (usa servicio existente)."""
    if not user.is_authenticated:
        return False
    return UserPermissionService.es_tecnico_o_abogado(user)


def get_comedores_del_tecnico(user):
    """
    Obtiene los comedores asignados a un técnico.
    Relación: User → Dupla (M2M) → Comedor (FK)
    """
    from comedores.models import Comedor
    # Obtener las duplas activas del técnico
    duplas = user.dupla_tecnico.filter(estado='Activo')
    # Obtener comedores de esas duplas
    return Comedor.objects.filter(dupla__in=duplas)


def get_comedores_del_usuario(user):
    """Retorna los comedores que puede ver/enviar el usuario."""
    from comedores.models import Comedor
    if is_admin(user) or _in_group(user, UserGroups.COMUNICADO_INTERNO_CREAR):
        # Admin y usuarios con permisos internos ven todos los comedores
        return Comedor.objects.all()
    elif es_tecnico(user):
        # Técnico ve solo los comedores de sus duplas
        return get_comedores_del_tecnico(user)
    return Comedor.objects.none()


# Permisos para comunicados internos
def can_create_comunicado_interno(user) -> bool:
    """Verifica si puede crear comunicados internos."""
    if not user.is_authenticated:
        return False
    return is_admin(user) or _in_group(user, UserGroups.COMUNICADO_INTERNO_CREAR)


def can_edit_comunicado_interno(user) -> bool:
    """Verifica si puede editar comunicados internos."""
    if not user.is_authenticated:
        return False
    return is_admin(user) or _in_group(user, UserGroups.COMUNICADO_INTERNO_EDITAR)


def can_publish_comunicado_interno(user) -> bool:
    """Verifica si puede publicar comunicados internos."""
    if not user.is_authenticated:
        return False
    return is_admin(user) or _in_group(user, UserGroups.COMUNICADO_INTERNO_PUBLICAR)


def can_archive_comunicado_interno(user) -> bool:
    """Verifica si puede archivar comunicados internos."""
    if not user.is_authenticated:
        return False
    return is_admin(user) or _in_group(user, UserGroups.COMUNICADO_INTERNO_ARCHIVAR)


# Permisos para comunicados a comedores (externos)
def can_create_comunicado_comedores(user) -> bool:
    """Admin, usuarios con permiso comedores, o técnicos pueden crear externos."""
    if not user.is_authenticated:
        return False
    return (is_admin(user) or
            _in_group(user, UserGroups.COMUNICADO_COMEDORES_CREAR) or
            es_tecnico(user))


def can_edit_comunicado_comedores(user) -> bool:
    """Verifica si puede editar comunicados a comedores."""
    if not user.is_authenticated:
        return False
    return (is_admin(user) or
            _in_group(user, UserGroups.COMUNICADO_COMEDORES_EDITAR) or
            es_tecnico(user))


def can_publish_comunicado_comedores(user) -> bool:
    """Verifica si puede publicar comunicados a comedores."""
    if not user.is_authenticated:
        return False
    return (is_admin(user) or
            _in_group(user, UserGroups.COMUNICADO_COMEDORES_PUBLICAR) or
            es_tecnico(user))


def can_archive_comunicado_comedores(user) -> bool:
    """Verifica si puede archivar comunicados a comedores."""
    if not user.is_authenticated:
        return False
    return (is_admin(user) or
            _in_group(user, UserGroups.COMUNICADO_COMEDORES_ARCHIVAR) or
            es_tecnico(user))
