from django.db.models.signals import post_save
from django.dispatch import receiver
from comedores.models import Relevamiento, Comedor
from comedores.services.relevamiento_service import RelevamientoService
from comedores.services.comedor_service import ComedorService


@receiver(post_save, sender=Comedor)
def send_comedor_to_gestionar(sender, instance, created, **kwargs):
    if created:
        ComedorService.send_to_gestionar(instance)


@receiver(post_save, sender=Relevamiento)
def send_relevamiento_to_gestionar(sender, instance, created, **kwargs):
    if created:
        RelevamientoService.send_to_gestionar(instance)
