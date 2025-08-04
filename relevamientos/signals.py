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


@receiver(pre_delete, sender=Relevamiento)
def remove_relevamiento_to_gestionar(sender, instance, using, **kwargs):
    AsyncRemoveRelevamientoToGestionar(instance.id).start()
