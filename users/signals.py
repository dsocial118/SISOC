from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import User, Group

from users.models import Profile
from core.constants import GROUP_INHERITANCE


@receiver(post_save, sender=User)
def ensure_user_profile(sender, instance, created, **kwargs):
    """Garantiza que cada usuario tenga exactamente un Profile asociado."""
    Profile.objects.get_or_create(user=instance)


@receiver(m2m_changed, sender=Profile.duplas_asignadas.through)
def sync_profile_duplas_to_dupla_coordinador(
    sender, instance, action, pk_set, **kwargs
):
    """
    Cuando se modifica Profile.duplas_asignadas desde el ABM de usuarios,
    sincroniza el campo Dupla.coordinador.

    Casos:
    - post_add: Se agregaron duplas -> actualizar Dupla.coordinador de esas duplas
    - post_remove: Se removieron duplas -> limpiar Dupla.coordinador de esas duplas
    - post_clear: Se limpiaron todas las duplas -> limpiar Dupla.coordinador de todas
    """
    from duplas.models import Dupla  # pylint: disable=import-outside-toplevel

    if action == "post_add":
        # Se agregaron duplas al coordinador
        if pk_set and hasattr(instance, "user"):
            # Actualizar el coordinador en cada dupla agregada
            Dupla.objects.filter(pk__in=pk_set).update(coordinador=instance.user)

    elif action == "post_remove":
        # Se removieron duplas del coordinador
        if pk_set and hasattr(instance, "user"):
            # Limpiar el coordinador solo si es este usuario
            Dupla.objects.filter(pk__in=pk_set, coordinador=instance.user).update(
                coordinador=None
            )

    elif action == "post_clear":
        # Se limpiaron todas las duplas del coordinador
        if hasattr(instance, "user"):
            # Limpiar el coordinador de todas las duplas que tengan a este usuario
            Dupla.objects.filter(coordinador=instance.user).update(coordinador=None)


def _assign_inherited_groups(user: User, inherited_names):
    if not inherited_names:
        return

    inherited_names = set(inherited_names)
    existing = set(
        user.groups.filter(name__in=inherited_names).values_list("name", flat=True)
    )
    missing = inherited_names - existing
    if not missing:
        return

    groups_to_add = Group.objects.filter(name__in=missing)
    if groups_to_add:
        user.groups.add(*groups_to_add)


@receiver(m2m_changed, sender=User.groups.through)
def ensure_inherited_groups(sender, instance, action, reverse, pk_set, **kwargs):
    """
    Garantiza que los grupos con roles heredados agreguen automáticamente
    los permisos base asociados. Si luego se elimina el rol coordinador,
    el usuario conserva los grupos heredados.
    """

    if action != "post_add" or not pk_set:
        return

    # Caso típico: se agregan grupos desde user.groups.add(...)
    if not reverse:
        added_names = set(
            Group.objects.filter(pk__in=pk_set).values_list("name", flat=True)
        )
        inherited = set()
        for name in added_names:
            inherited.update(GROUP_INHERITANCE.get(name, []))

        if inherited:
            _assign_inherited_groups(instance, inherited)
        return

    # Caso inverso: se agregan usuarios desde group.user_set.add(...)
    group_name = getattr(instance, "name", None)
    inherited = GROUP_INHERITANCE.get(group_name)
    if not inherited:
        return

    users = User.objects.filter(pk__in=pk_set)
    for user in users:
        _assign_inherited_groups(user, inherited)
