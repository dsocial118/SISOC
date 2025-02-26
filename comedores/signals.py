from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from comedores.models.comedor import Observacion, Referente, Comedor
from comedores.models.relevamiento import Relevamiento
from comedores.services.clasificacion_comedor_service import ClasificacionComedorService
from comedores.tasks import (
    AsyncRemoveComedorToGestionar,
    AsyncRemoveRelevamientoToGestionar,
    AsyncSendComedorToGestionar,
    AsyncSendObservacionToGestionar,
    AsyncSendReferenteToGestionar,
    AsyncSendRelevamientoToGestionar,
)


@receiver(post_save, sender=Comedor)
def send_comedor_to_gestionar(sender, instance, created, **kwargs):
    if created:
        AsyncSendComedorToGestionar(instance.id).start()


@receiver(pre_save, sender=Comedor)
def update_comedor_in_gestionar(sender, instance, **kwargs):
    if instance.pk:  # Solo para updates
        previous_instance = sender.objects.get(pk=instance.pk)
        for field in instance._meta.fields:
            field_name = field.name
            new_value = getattr(instance, field_name)
            old_value = getattr(previous_instance, field_name)

            if field_name == "foto_legajo" and not new_value:
                continue  # Ignorar cambios en foto_legajo si está vacío

            if new_value != old_value:
                AsyncSendComedorToGestionar(instance.id).start()
                break


@receiver(pre_delete, sender=Comedor)
def remove_comedor_to_gestionar(sender, instance, using, **kwargs):
    AsyncRemoveComedorToGestionar(instance.id).start()


@receiver(post_save, sender=Relevamiento)
def send_relevamiento_to_gestionar(sender, instance, created, **kwargs):
    if created:
        AsyncSendRelevamientoToGestionar(instance.id).start()


@receiver(pre_delete, sender=Relevamiento)
def remove_relevamiento_to_gestionar(sender, instance, using, **kwargs):
    AsyncRemoveRelevamientoToGestionar(instance.id).start()


@receiver(post_save, sender=Observacion)
def send_observacion_to_gestionar(sender, instance, created, **kwargs):
    if created:
        AsyncSendObservacionToGestionar(instance.id).start()


@receiver(post_save, sender=Referente)
def send_referente_to_gestionar(sender, instance, created, **kwargs):
    if created:
        AsyncSendReferenteToGestionar(instance.id).start()


@receiver(post_save, sender=Relevamiento)
def clasificacion_relevamiento(sender, instance, **kwargs):
    ClasificacionComedorService.create_clasificacion_relevamiento(instance)
