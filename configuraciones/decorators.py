from django.contrib.auth.decorators import user_passes_test


def group_required(group_name):
    """
    Permite el acceso solo a usuarios autenticados que pertenezcan al grupo indicado,
    o que sean superusuarios.
    """

    def in_group(user):
        return user.is_authenticated and (
            user.groups.filter(name=group_name).exists() or user.is_superuser
        )

    return user_passes_test(in_group)
