import logging

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import (
    HistorialAlerta,
    Alerta,
    CiudadanoPrograma,
    HistorialCiudadanoProgramas,
)

# guardado de log de usuarios
logger = logging.getLogger("django")


@receiver(post_save, sender=Alerta)
def alertas_is_created(sender, instance, created, **kwargs):
    """
    Guardado de historial cuando se produzca la creación o modificación de un alerta asociadas a un Ciudadano.
    """
    registro = HistorialAlerta.objects.create(
        alerta=instance.alerta,
        ciudadano=instance.ciudadano,
        observaciones=instance.observaciones,
        creada_por=instance.creada_por,
    )
    registro.save()


@receiver(post_save, sender=CiudadanoPrograma)
def registrar_agregado_en_historial(sender, instance, created, **kwargs):
    if created:  # Solo registrar si es un nuevo registro
        HistorialCiudadanoProgramas.objects.create(
            programa=instance.programas,
            ciudadano=instance.ciudadano,
            accion="agregado",
            usuario=(instance.creado_por if instance.creado_por else "Desconocido"),
        )


@receiver(post_delete, sender=CiudadanoPrograma)
def registrar_eliminacion_en_historial(sender, instance, **kwargs):
    HistorialCiudadanoProgramas.objects.create(
        programa=instance.programas,
        ciudadano=instance.ciudadano,
        accion="eliminado",
        usuario=instance.creado_por if instance.creado_por else "Desconocido",
    )
