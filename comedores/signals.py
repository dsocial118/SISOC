from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from comedores.models.comedor import Observacion, Referente, Comedor
from comedores.models.relevamiento import Relevamiento
from comedores.services.observacion_service import ObservacionService
from comedores.services.relevamiento_service import RelevamientoService
from comedores.services.comedor_service import ComedorService


@receiver(post_save, sender=Comedor)
def send_comedor_to_gestionar(sender, instance, created, update_fields, **kwargs):
    if created or update_fields:
        ComedorService.send_to_gestionar(instance)


@receiver(pre_delete, sender=Comedor)
def remove_comedor_to_gestionar(sender, instance, using, **kwargs):
    ComedorService.remove_to_gestionar(instance)


@receiver(post_save, sender=Relevamiento)
def send_relevamiento_to_gestionar(sender, instance, created, update_fields, **kwargs):
    if created or update_fields:
        RelevamientoService.send_to_gestionar(instance)


@receiver(pre_delete, sender=Relevamiento)
def remove_relevamiento_to_gestionar(sender, instance, using, **kwargs):
    RelevamientoService.remove_to_gestionar(instance)


@receiver(post_save, sender=Observacion)
def send_observacion_to_gestionar(sender, instance, created, **kwargs):
    if created:
        ObservacionService.send_to_gestionar(instance)


@receiver(post_save, sender=Referente)
def send_referente_to_gestionar(sender, instance, created, **kwargs):
    if created:
        ComedorService.send_referente_to_gestionar(instance)
