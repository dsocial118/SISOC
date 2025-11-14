from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import User

from users.models import Profile


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
