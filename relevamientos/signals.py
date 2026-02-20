from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from relevamientos.models import Relevamiento
from relevamientos.tasks import (
    AsyncSendRelevamientoToGestionar,
    AsyncRemoveRelevamientoToGestionar,
    build_relevamiento_payload,
)
from core.soft_delete_signals import post_soft_delete


@receiver(post_save, sender=Relevamiento)
def send_relevamiento_to_gestionar(sender, instance, created, **kwargs):
    if created:
        payload = build_relevamiento_payload(instance)
        AsyncSendRelevamientoToGestionar(instance.id, payload).start()


@receiver(post_save, sender=Relevamiento)
def update_comedor_geolocalizacion(sender, instance, created, **kwargs):
    """
    Actualiza la geolocalización del comedor cuando el relevamiento está finalizado
    y tiene datos de excepción con latitud/longitud. n
    """
    if instance.estado in ["Finalizado", "Finalizado/Excepciones"]:
        if instance.excepcion and instance.comedor:
            if instance.excepcion.latitud and instance.excepcion.longitud:
                comedor = instance.comedor
                comedor.latitud = instance.excepcion.latitud
                comedor.longitud = instance.excepcion.longitud
                comedor.save(update_fields=["latitud", "longitud"])


@receiver(pre_delete, sender=Relevamiento)
@receiver(post_soft_delete, sender=Relevamiento)
def remove_relevamiento_to_gestionar(sender, instance, **kwargs):
    AsyncRemoveRelevamientoToGestionar(instance.id).start()
