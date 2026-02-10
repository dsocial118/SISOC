"""
Módulo centralizado para validaciones de permisos en comunicados.
"""

from django.core.exceptions import PermissionDenied
from core.constants import UserGroups


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
