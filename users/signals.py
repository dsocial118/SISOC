from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import Group, User

from core.constants import GROUP_INHERITANCE
from users.models import Profile
from users.services_group_permissions import sync_permissions_for_group


@receiver(post_save, sender=User)
def ensure_user_profile(sender, instance, created, **kwargs):
    """
    Garantiza que cada usuario tenga exactamente un Profile asociado.
    - Crea el perfil cuando se crea el usuario.
    - Vuelve a generarlo si se eliminó manualmente y persiste los cambios.
    """
    if created:
        Profile.objects.create(user=instance)
        return

    profile, _ = Profile.objects.get_or_create(user=instance)
    profile.save()


@receiver(post_save, sender=Group)
def ensure_group_permission(sender, instance, created, **kwargs):
    if created:
        sync_permissions_for_group(instance)


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
        added_groups = Group.objects.filter(pk__in=pk_set)
        for group in added_groups:
            sync_permissions_for_group(group)

        added_names = set(added_groups.values_list("name", flat=True))
        inherited = set()
        for name in added_names:
            inherited.update(GROUP_INHERITANCE.get(name, []))

        if inherited:
            _assign_inherited_groups(instance, inherited)
        return

    # Caso inverso: se agregan usuarios desde group.user_set.add(...)
    group_name = getattr(instance, "name", None)
    sync_permissions_for_group(instance)
    inherited = GROUP_INHERITANCE.get(group_name)
    if not inherited:
        return

    users = User.objects.filter(pk__in=pk_set)
    for user in users:
        _assign_inherited_groups(user, inherited)
