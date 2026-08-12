"""Eventos de auditoría que pertenecen al dominio Comedores."""

from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from audittrail.api import ACTION_CREATE, ACTION_DELETE, ACTION_UPDATE, registrar_evento
from comedores.models import Comedor, ImagenComedor, Referente


REFERENTE_FIELDS = ("nombre", "apellido", "mail", "celular", "documento", "funcion")


@receiver(pre_save, sender=Referente)
def cache_referente_state(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        instance._audittrail_previous_state = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        instance._audittrail_previous_state = None


@receiver(post_save, sender=Referente)
def registrar_cambios_referente(sender, instance, created: bool, **kwargs):
    if created:
        return

    previous = getattr(instance, "_audittrail_previous_state", None)
    changes = {}
    if previous:
        for field_name in REFERENTE_FIELDS:
            old, new = getattr(previous, field_name), getattr(instance, field_name)
            if old != new:
                verbose = sender._meta.get_field(field_name).verbose_name
                changes[f"Referente: {verbose}"] = [old, new]
    if hasattr(instance, "_audittrail_previous_state"):
        delattr(instance, "_audittrail_previous_state")
    if not changes:
        return
    for comedor in Comedor.objects.filter(referente=instance):
        registrar_evento(comedor, changes, ACTION_UPDATE)


@receiver(pre_save, sender=ImagenComedor)
def cache_imagen_comedor_state(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        previous = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        previous = None
    if previous:
        instance._audittrail_previous_image = {
            "imagen": previous.imagen.name if previous.imagen else "",
            "comedor_id": previous.comedor_id,
        }


@receiver(post_save, sender=ImagenComedor)
def registrar_cambios_imagen_comedor(sender, instance, created: bool, **kwargs):
    image_name = instance.imagen.name if instance.imagen else ""
    if created:
        registrar_evento(
            instance.comedor,
            {"Imagen": [None, image_name or "Imagen creada"]},
            ACTION_CREATE,
        )
        return

    previous = getattr(instance, "_audittrail_previous_image", None)
    changes = {}
    if previous:
        if previous["imagen"] != image_name:
            changes["Imagen"] = [
                previous["imagen"] or "Sin imagen",
                image_name or "Sin imagen",
            ]
        if previous["comedor_id"] != instance.comedor_id:
            changes["Imagen: Comedor"] = [
                previous["comedor_id"],
                instance.comedor_id,
            ]
    if hasattr(instance, "_audittrail_previous_image"):
        delattr(instance, "_audittrail_previous_image")
    if changes:
        registrar_evento(instance.comedor, changes, ACTION_UPDATE)


@receiver(post_delete, sender=ImagenComedor)
def registrar_baja_imagen_comedor(sender, instance, **kwargs):
    image_name = instance.imagen.name if instance.imagen else "Imagen eliminada"
    registrar_evento(
        instance.comedor,
        {"Imagen": [image_name, "Eliminada"]},
        ACTION_DELETE,
    )
