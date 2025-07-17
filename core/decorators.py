from functools import wraps

from django.core.exceptions import PermissionDenied


def group_required(group_names):
    """
    Permite el acceso solo a usuarios autenticados que pertenezcan a alguno de los grupos indicados,
    o que sean superusuarios.
    """

    def in_group(user):
        return user.is_authenticated and (
            user.groups.filter(name__in=group_names).exists() or user.is_superuser
        )

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            is_in = in_group(request.user)
            if not is_in:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator
