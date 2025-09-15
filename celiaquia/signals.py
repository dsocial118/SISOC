from django.db.models.signals import pre_save
from django.dispatch import receiver

from config.middlewares.threadlocals import get_current_user
from .models import Expediente, ExpedienteEstadoHistorial


@receiver(pre_save, sender=Expediente)
def registrar_historial_estado(sender, instance, **_):
    """Registra el historial cuando cambia el estado de un expediente."""
    if not instance.pk:
        return
    try:
        previous = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:  # pragma: no cover - race condition
        return
    if previous.estado_id != instance.estado_id:
        ExpedienteEstadoHistorial.objects.create(
            expediente=instance,
            estado_anterior=previous.estado,
            estado_nuevo=instance.estado,
            usuario=get_current_user(),
        )
