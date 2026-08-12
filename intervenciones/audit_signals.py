"""Eventos de auditoría que pertenecen al flujo de Intervenciones."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from audittrail.api import ACTION_CREATE, registrar_evento
from intervenciones.models.intervenciones import Intervencion


@receiver(post_save, sender=Intervencion)
def registrar_alta_intervencion(sender, instance, created: bool, **kwargs):
    """Registra la creación de una intervención en el legajo del comedor."""

    if not created or not instance.comedor:
        return

    descripcion = f"Intervención #{instance.pk}"
    if instance.tipo_intervencion:
        descripcion = f"{descripcion} - {instance.tipo_intervencion}"
    registrar_evento(
        instance.comedor,
        {"Intervención": [None, descripcion]},
        ACTION_CREATE,
    )
