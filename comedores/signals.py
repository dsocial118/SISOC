from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from comedores.models.comedor import Observacion, Referente, Comedor
from comedores.models.relevamiento import Relevamiento
from comedores.services.observacion_service import ObservacionService
from comedores.services.relevamiento_service import RelevamientoService
from comedores.services.comedor_service import ComedorService
from comedores.services.clasificacion_comedor_service import ClasificacionComedorService

@receiver(post_save, sender=Comedor)
def send_comedor_to_gestionar(sender, instance, created, update_fields, **kwargs):
    if created:
        ComedorService.send_to_gestionar(instance)


@receiver(pre_save, sender=Comedor)
def update_comedor_in_gestionar(sender, instance, **kwargs):
    if instance.pk:  # Solo para updates
        previous_instance = sender.objects.get(pk=instance.pk)
        for field in instance._meta.fields:
            field_name = field.name
            if getattr(instance, field_name) != getattr(previous_instance, field_name):
                ComedorService.send_to_gestionar(instance)
                break


@receiver(pre_delete, sender=Comedor)
def remove_comedor_to_gestionar(sender, instance, using, **kwargs):
    ComedorService.remove_to_gestionar(instance)


@receiver(post_save, sender=Relevamiento)
def send_relevamiento_to_gestionar(sender, instance, created, **kwargs):
    if created:
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

@receiver(post_save, sender=Relevamiento)
def clasificacion_relevamiento(sender, instance, **kwargs):
  ClasificacionComedorService.create_clasificacion_relevamiento(instance)
