"""Eventos de auditoría que pertenecen al flujo de Admisiones."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from admisiones.models.admisiones import Admision
from audittrail.api import ACTION_CREATE, registrar_evento


@receiver(post_save, sender=Admision)
def registrar_alta_admision(sender, instance, created: bool, **kwargs):
    """Registra la creación de una admisión en el legajo del comedor."""

    if not created or not instance.comedor:
        return

    descripcion = f"Admisión #{instance.pk}"
    if instance.estado_mostrar:
        descripcion = f"{descripcion} ({instance.estado_mostrar})"
    registrar_evento(instance.comedor, {"Admisión": [None, descripcion]}, ACTION_CREATE)
