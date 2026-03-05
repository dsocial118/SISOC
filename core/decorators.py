from functools import wraps

from django.core.exceptions import PermissionDenied

from core.permissions.registry import resolve_permission_codes
from iam.services import user_has_permission_code


def _is_authenticated(user):
    return bool(user and getattr(user, "is_authenticated", False))


def _has_any_permissions(user, permission_aliases):
    if not _is_authenticated(user):
        return False
    if getattr(user, "is_superuser", False):
        return True

    permission_codes = resolve_permission_codes(permission_aliases)
    return any(user_has_permission_code(user, code) for code in permission_codes)


def _has_all_permissions(user, permission_aliases):
    if not _is_authenticated(user):
        return False
    if getattr(user, "is_superuser", False):
        return True

    permission_codes = resolve_permission_codes(permission_aliases)
    if not permission_codes:
        return False
    return all(user_has_permission_code(user, code) for code in permission_codes)


def permissions_any_required(permission_aliases):
    """Permite acceso cuando el usuario posee al menos un permiso indicado."""

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not _has_any_permissions(request.user, permission_aliases):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def permissions_all_required(permission_aliases):
    """Permite acceso cuando el usuario posee todos los permisos indicados."""

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not _has_all_permissions(request.user, permission_aliases):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def permission_code_required(permission_code):
    """Alias para mantener compatibilidad de imports existentes."""
    return permissions_all_required([permission_code])
