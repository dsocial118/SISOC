"""
Signals para mantener la sincronización bidireccional entre Dupla y Profile.

La relación coordinador <-> duplas es bidireccional:
- Dupla.coordinador (ForeignKey)
- Profile.duplas_asignadas (ManyToMany)

Estos signals aseguran que cuando se modifica uno, el otro se actualice automáticamente.
"""

from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from duplas.models import Dupla


@receiver(pre_save, sender=Dupla)
def capture_old_coordinador(sender, instance, **kwargs):
    """
    Captura el coordinador anterior antes de guardar para poder
    actualizar la relación M2M en post_save.
    """
    if instance.pk:
        try:
            old_dupla = Dupla.objects.get(pk=instance.pk)
            # pylint: disable=protected-access
            instance._old_coordinador_id = old_dupla.coordinador_id
        except Dupla.DoesNotExist:
            instance._old_coordinador_id = None  # pylint: disable=protected-access
    else:
        instance._old_coordinador_id = None  # pylint: disable=protected-access


@receiver(post_save, sender=Dupla)
def sync_dupla_coordinador_to_profile(sender, instance, created, **kwargs):
    """
    Cuando se guarda una Dupla, sincroniza el coordinador con Profile.duplas_asignadas.

    Casos:
    1. Se asigna un coordinador nuevo -> agregar esta dupla a su perfil
    2. Se cambia el coordinador -> remover de perfil anterior y agregar al nuevo
    3. Se remueve el coordinador -> remover esta dupla del perfil anterior
    """
    new_coordinador = instance.coordinador
    old_coordinador_id = getattr(instance, "_old_coordinador_id", None)

    # Si no cambió el coordinador, no hacer nada
    if not created and old_coordinador_id == (
        new_coordinador.id if new_coordinador else None
    ):
        return

    # Remover de coordinador anterior si existe
    if old_coordinador_id:
        try:
            # pylint: disable=import-outside-toplevel
            from django.contrib.auth.models import User

            old_coordinador = User.objects.get(pk=old_coordinador_id)
            if hasattr(old_coordinador, "profile"):
                old_coordinador.profile.duplas_asignadas.remove(instance)
        except User.DoesNotExist:
            pass

    # Agregar a coordinador nuevo si existe
    if new_coordinador:
        if hasattr(new_coordinador, "profile"):
            # Verificar que no esté ya agregado (para evitar duplicados)
            if not new_coordinador.profile.duplas_asignadas.filter(
                pk=instance.pk
            ).exists():
                new_coordinador.profile.duplas_asignadas.add(instance)


@receiver(post_delete, sender=Dupla)
def remove_dupla_from_coordinador_profile(sender, instance, **kwargs):
    """
    Cuando se elimina una Dupla, removerla del perfil del coordinador.
    """
    if instance.coordinador:
        if hasattr(instance.coordinador, "profile"):
            instance.coordinador.profile.duplas_asignadas.remove(instance)
