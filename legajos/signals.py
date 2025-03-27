import logging

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import (
    HistorialLegajoAlertas,
    LegajoAlertas,
    LegajoProgramas,
    HistorialLegajoProgramas,
)

# guardado de log de usuarios
logger = logging.getLogger("django")


@receiver(post_save, sender=LegajoAlertas)
def legajoalertas_is_created(sender, instance, created, **kwargs):
    """
    Guardado de historial cuando se produzca la creación o modificación de un alerta asociadas a un Legajo.
    """
    registro = HistorialLegajoAlertas.objects.create(
        alerta=instance.alerta,
        legajo=instance.legajo,
        observaciones=instance.observaciones,
        creada_por=instance.creada_por,
    )
    registro.save()


@receiver(post_save, sender=LegajoProgramas)
def registrar_agregado_en_historial(sender, instance, created, **kwargs):
    if created:  # Solo registrar si es un nuevo registro
        HistorialLegajoProgramas.objects.create(
            programa=instance.programas,
            legajo=instance.legajo,
            accion="agregado",
            usuario=(instance.creado_por if instance.creado_por else "Desconocido"),
        )


@receiver(post_delete, sender=LegajoProgramas)
def registrar_eliminacion_en_historial(sender, instance, **kwargs):
    HistorialLegajoProgramas.objects.create(
        programa=instance.programas,
        legajo=instance.legajo,
        accion="eliminado",
        usuario=instance.creado_por if instance.creado_por else "Desconocido",
    )
