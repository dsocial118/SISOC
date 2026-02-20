from django.db import transaction
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from comedores.models import Observacion, Referente, Comedor, AuditComedorPrograma
from comedores.services.clasificacion_comedor_service import ClasificacionComedorService
from comedores.tasks import (
    AsyncRemoveComedorToGestionar,
    AsyncSendComedorToGestionar,
    AsyncSendObservacionToGestionar,
    AsyncSendReferenteToGestionar,
    build_comedor_payload,
    build_observacion_payload,
    build_referente_payload,
)
from relevamientos.models import Relevamiento
from rendicioncuentasfinal.models import (
    DocumentoRendicionFinal,
    RendicionCuentasFinal,
    TipoDocumentoRendicionFinal,
)
from config.middlewares.threadlocals import get_current_user
from core.soft_delete_signals import post_soft_delete


@receiver(post_save, sender=Comedor)
def send_comedor_to_gestionar(sender, instance, created, **kwargs):
    if created:
        payload = build_comedor_payload(instance)  # usa los NEW values de la instancia
        AsyncSendComedorToGestionar(payload).start()


@receiver(pre_save, sender=Comedor)
def update_comedor_in_gestionar(sender, instance, **kwargs):
    if not instance.pk:
        return
    previous = sender.objects.get(pk=instance.pk)

    programa_changed = previous.programa_id != instance.programa_id
    if programa_changed:
        previous_programa_id = previous.programa_id
        new_programa_id = instance.programa_id
        current_user = get_current_user()
        current_user_id = getattr(current_user, "pk", None)

        transaction.on_commit(
            lambda: AuditComedorPrograma.objects.create(
                comedor=instance,
                from_programa_id=previous_programa_id,
                to_programa_id=new_programa_id,
                changed_by_id=current_user_id,
            )
        )

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
@receiver(post_soft_delete, sender=Comedor)
def remove_comedor_to_gestionar(sender, instance, **kwargs):
    AsyncRemoveComedorToGestionar(instance.id).start()


@receiver(post_save, sender=Observacion)
def send_observacion_to_gestionar(sender, instance, created, **kwargs):
    if created:
        payload = build_observacion_payload(instance)
        AsyncSendObservacionToGestionar(instance.id, payload).start()


@receiver(post_save, sender=Referente)
def send_referente_to_gestionar(sender, instance, created, **kwargs):
    if created:
        payload = build_referente_payload(instance)
        AsyncSendReferenteToGestionar(instance.id, payload).start()


@receiver(post_save, sender=RendicionCuentasFinal)
def crear_documentos_por_defecto(sender, instance, created, **kwargs):
    if created:
        for tipo in TipoDocumentoRendicionFinal.objects.filter(personalizado=False):
            DocumentoRendicionFinal.objects.create(rendicion_final=instance, tipo=tipo)


@receiver(post_save, sender=Relevamiento)
def clasificacion_relevamiento(sender, instance, **kwargs):
    ClasificacionComedorService.create_clasificacion_relevamiento(instance)
