from django.contrib.auth.decorators import user_passes_test


def group_required(*group_names):
    """
    Permite el acceso solo a usuarios autenticados que pertenezcan a alguno de los grupos indicados,
    o que sean superusuarios.
    """

    def in_group(user):
        return user.is_authenticated and (
            user.groups.filter(name__in=group_names).exists() or user.is_superuser
        )

    return user_passes_test(in_group)
