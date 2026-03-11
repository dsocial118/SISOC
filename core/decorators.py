from functools import wraps

from django.core.exceptions import PermissionDenied

from iam.services import user_has_permission_code


def _is_authenticated(user):
    return bool(user and getattr(user, "is_authenticated", False))


def _has_any_permissions(user, permission_codes):
    if not _is_authenticated(user):
        return False
    if getattr(user, "is_superuser", False):
        return True

    return any(
        user_has_permission_code(user, code) for code in (permission_codes or [])
    )


def _has_all_permissions(user, permission_codes):
    if not _is_authenticated(user):
        return False
    if getattr(user, "is_superuser", False):
        return True

    requested = list(permission_codes or [])
    if not requested:
        return False
    return all(user_has_permission_code(user, code) for code in requested)


def permissions_any_required(permission_codes):
    """Permite acceso cuando el usuario posee al menos un permiso indicado."""

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not _has_any_permissions(request.user, permission_codes):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def permissions_all_required(permission_codes):
    """Permite acceso cuando el usuario posee todos los permisos indicados."""

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not _has_all_permissions(request.user, permission_codes):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def permission_code_required(permission_code):
    """Alias para mantener compatibilidad de imports existentes."""
    return permissions_all_required([permission_code])
