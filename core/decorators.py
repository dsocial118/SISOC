from functools import wraps

from django.core.exceptions import PermissionDenied


def group_required(group_names):
    def in_group(user):
        return user.is_authenticated and (
            user.groups.filter(name__in=group_names).exists() or user.is_superuser
        )

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not in_group(request.user):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator