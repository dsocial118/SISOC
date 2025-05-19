from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from intervenciones.models.intervenciones import (
    Intervencion,
    SubIntervencion,
    TipoIntervencion,
    TipoDestinatario,
)
from acompanamientos.acompanamiento_service import AcompanamientoService

@receiver(post_save, sender=Intervencion)
def crear_hitos(sender, instance, **kwargs):
    print("Creando hitos para la intervención")
    AcompanamientoService.crear_hitos(instance)