from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from relevamientos.models import Relevamiento
from relevamientos.tasks import (
    AsyncSendRelevamientoToGestionar,
    AsyncRemoveRelevamientoToGestionar,
)


@receiver(post_save, sender=Relevamiento)
def send_relevamiento_to_gestionar(sender, instance, created, **kwargs):
    if created:
        AsyncSendRelevamientoToGestionar(instance.id).start()


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
def remove_relevamiento_to_gestionar(sender, instance, using, **kwargs):
    AsyncRemoveRelevamientoToGestionar(instance.id).start()
