"""Resolución declarativa del alcance efectivo de delegación de grupos."""

from django.contrib.auth.models import Group

from core.constants import GROUP_DELEGATION


def effective_delegatable_group_ids(user) -> set[int]:
    """Retorna grupos delegables manuales y derivados del rol del usuario.

    No persiste los grupos derivados: el mapa declarativo se evalúa en cada
    consulta para conservar ``Profile.grupos_asignables`` como configuración
    manual explícita.
    """
    if not user or not getattr(user, "pk", None):
        return set()

    profile = getattr(user, "profile", None)
    group_ids = (
        set(profile.grupos_asignables.values_list("id", flat=True))
        if profile
        else set()
    )

    delegated_group_names = {
        delegated_group_name
        for group_name in user.groups.values_list("name", flat=True)
        for delegated_group_name in GROUP_DELEGATION.get(group_name, ())
    }
    if delegated_group_names:
        group_ids.update(
            Group.objects.filter(name__in=delegated_group_names).values_list(
                "id", flat=True
            )
        )

    return group_ids


def effective_delegatable_groups_qs(user):
    """Retorna un queryset de los grupos delegables efectivos del usuario."""
    return Group.objects.filter(pk__in=effective_delegatable_group_ids(user))
