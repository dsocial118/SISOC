"""Eventos de auditoría que pertenecen al dominio Organizaciones."""

from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from audittrail.api import ACTION_CREATE, ACTION_DELETE, ACTION_UPDATE, registrar_evento
from core.soft_delete.signals import post_soft_delete
from organizaciones.models import Aval, Firmante


def _mark_delete_event_logged(instance) -> bool:
    if getattr(instance, "_audittrail_delete_logged", False):
        return True
    instance._audittrail_delete_logged = True
    return False


def _registrar_baja_relacionada(instance, label: str):
    if not instance.organizacion or _mark_delete_event_logged(instance):
        return
    registrar_evento(
        instance.organizacion,
        {label: [str(instance), "Eliminado"]},
        ACTION_DELETE,
    )


@receiver(pre_save, sender=Firmante)
def cache_firmante_state(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        instance._audittrail_previous_state = sender.objects.select_related(
            "rol", "organizacion"
        ).get(pk=instance.pk)
    except sender.DoesNotExist:
        instance._audittrail_previous_state = None


@receiver(post_save, sender=Firmante)
def registrar_cambios_firmante(sender, instance, created: bool, **kwargs):
    if not instance.organizacion:
        return
    if created:
        registrar_evento(
            instance.organizacion,
            {"Firmante": [None, str(instance)]},
            ACTION_CREATE,
        )
        return
    previous = getattr(instance, "_audittrail_previous_state", None)
    changes = {}
    if previous:
        if previous.nombre != instance.nombre:
            changes["Firmante: Nombre"] = [previous.nombre, instance.nombre]
        if previous.cuit != instance.cuit:
            changes["Firmante: CUIT"] = [previous.cuit, instance.cuit]
        if previous.rol_id != instance.rol_id:
            changes["Firmante: Rol"] = [
                str(previous.rol) if previous.rol else None,
                str(instance.rol) if instance.rol else None,
            ]
    if hasattr(instance, "_audittrail_previous_state"):
        delattr(instance, "_audittrail_previous_state")
    if changes:
        registrar_evento(instance.organizacion, changes, ACTION_UPDATE)


@receiver(pre_save, sender=Aval)
def cache_aval_state(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        instance._audittrail_previous_state = sender.objects.select_related(
            "organizacion"
        ).get(pk=instance.pk)
    except sender.DoesNotExist:
        instance._audittrail_previous_state = None


@receiver(post_save, sender=Aval)
def registrar_cambios_aval(sender, instance, created: bool, **kwargs):
    if not instance.organizacion:
        return
    if created:
        registrar_evento(
            instance.organizacion,
            {"Aval": [None, str(instance)]},
            ACTION_CREATE,
        )
        return
    previous = getattr(instance, "_audittrail_previous_state", None)
    changes = {}
    if previous:
        if previous.nombre != instance.nombre:
            changes["Aval: Nombre"] = [previous.nombre, instance.nombre]
        if previous.cuit != instance.cuit:
            changes["Aval: CUIT"] = [previous.cuit, instance.cuit]
    if hasattr(instance, "_audittrail_previous_state"):
        delattr(instance, "_audittrail_previous_state")
    if changes:
        registrar_evento(instance.organizacion, changes, ACTION_UPDATE)


@receiver(post_soft_delete, sender=Firmante)
@receiver(post_delete, sender=Firmante)
def registrar_baja_firmante(sender, instance, **kwargs):
    _registrar_baja_relacionada(instance, "Firmante")


@receiver(post_soft_delete, sender=Aval)
@receiver(post_delete, sender=Aval)
def registrar_baja_aval(sender, instance, **kwargs):
    _registrar_baja_relacionada(instance, "Aval")
