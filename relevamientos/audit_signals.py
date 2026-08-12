"""Eventos de auditoría que pertenecen al flujo de Relevamientos."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from audittrail.api import ACTION_CREATE, registrar_evento
from relevamientos.models import Relevamiento


@receiver(post_save, sender=Relevamiento)
def registrar_alta_relevamiento(sender, instance, created: bool, **kwargs):
    """Registra la creación de un relevamiento en el legajo del comedor."""

    if not created or not instance.comedor:
        return

    fecha = instance.fecha_visita
    descripcion = f"Relevamiento #{instance.pk}"
    if fecha:
        descripcion = f"{descripcion} - {fecha:%Y-%m-%d}"
    registrar_evento(
        instance.comedor,
        {"Relevamiento": [None, descripcion]},
        ACTION_CREATE,
    )
