"""Eventos de auditoría que pertenecen al dominio Centro de Infancia."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from audittrail.api import ACTION_CREATE, registrar_evento
from centrodeinfancia.models import (
    FormularioCDI,
    IntervencionCentroInfancia,
    NominaCentroInfancia,
)


@receiver(post_save, sender=NominaCentroInfancia)
def registrar_alta_nomina(sender, instance, created: bool, **kwargs):
    if not created or not instance.centro:
        return

    descripcion = f"Nómina #{instance.pk}"
    if instance.ciudadano_id:
        descripcion = f"{descripcion} - {instance.ciudadano}"
    registrar_evento(instance.centro, {"Nómina": [None, descripcion]}, ACTION_CREATE)


@receiver(post_save, sender=IntervencionCentroInfancia)
def registrar_alta_intervencion(sender, instance, created: bool, **kwargs):
    if not created or not instance.centro:
        return

    descripcion = f"Intervención #{instance.pk}"
    if instance.tipo_intervencion:
        descripcion = f"{descripcion} - {instance.tipo_intervencion}"
    registrar_evento(
        instance.centro,
        {"Intervención": [None, descripcion]},
        ACTION_CREATE,
    )


@receiver(post_save, sender=FormularioCDI)
def registrar_alta_formulario(sender, instance, created: bool, **kwargs):
    if not created or not instance.centro:
        return

    descripcion = f"Formulario CDI #{instance.pk}"
    if instance.fecha_relevamiento:
        descripcion = f"{descripcion} - {instance.fecha_relevamiento:%Y-%m-%d}"
    registrar_evento(
        instance.centro,
        {"Formulario CDI": [None, descripcion]},
        ACTION_CREATE,
    )
