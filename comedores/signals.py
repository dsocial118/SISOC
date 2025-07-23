from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from comedores.models import (
    Observacion,
    Referente,
    Comedor,
)
from comedores.services.clasificacion_comedor_service import ClasificacionComedorService
from comedores.tasks import (
    AsyncRemoveComedorToGestionar,
    AsyncSendComedorToGestionar,
    AsyncSendObservacionToGestionar,
    AsyncSendReferenteToGestionar,
    build_comedor_payload,
)
from relevamientos.models import Relevamiento
from rendicioncuentasfinal.models import (
    DocumentoRendicionFinal,
    RendicionCuentasFinal,
    TipoDocumentoRendicionFinal,
)


@receiver(post_save, sender=Comedor)
def send_comedor_to_gestionar(sender, instance, created, **kwargs):
    if created:
        AsyncSendComedorToGestionar(instance.id).start()


@receiver(pre_save, sender=Comedor)
def update_comedor_in_gestionar(sender, instance, **kwargs):
    if not instance.pk:
        return
    previous = sender.objects.get(pk=instance.pk)

    changed = any(
        f.name not in {"foto_legajo"}
        and getattr(instance, f.name) != getattr(previous, f.name)
        for f in instance._meta.fields
    )
    if not changed:
        return

    payload = build_comedor_payload(instance)  # usa los NEW values de la instancia
    AsyncSendComedorToGestionar(payload).start()


@receiver(pre_delete, sender=Comedor)
def remove_comedor_to_gestionar(sender, instance, using, **kwargs):
    AsyncRemoveComedorToGestionar(instance.id).start()


@receiver(post_save, sender=Observacion)
def send_observacion_to_gestionar(sender, instance, created, **kwargs):
    if created:
        AsyncSendObservacionToGestionar(instance.id).start()


@receiver(post_save, sender=Referente)
def send_referente_to_gestionar(sender, instance, created, **kwargs):
    if created:
        AsyncSendReferenteToGestionar(instance.id).start()


@receiver(post_save, sender=RendicionCuentasFinal)
def crear_documentos_por_defecto(sender, instance, created, **kwargs):
    if created:
        for tipo in TipoDocumentoRendicionFinal.objects.filter(personalizado=False):
            DocumentoRendicionFinal.objects.create(rendicion_final=instance, tipo=tipo)


@receiver(post_save, sender=Relevamiento)
def clasificacion_relevamiento(sender, instance, **kwargs):
    ClasificacionComedorService.create_clasificacion_relevamiento(instance)
