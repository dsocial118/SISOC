from django.db.models.signals import post_save, post_delete,pre_delete
from django.dispatch import receiver
from django.utils.timezone import now
import logging
from .models import *

# guardado de log de usuarios
logger = logging.getLogger('django')

@receiver(post_save, sender=LegajoAlertas)
def legajoalertas_is_created(sender, instance, created, **kwargs):
    '''
    Guardado de historial cuando se produzca la creación o modificación de un alerta asociadas a un Legajo.
    '''
    registro = HistorialLegajoAlertas.objects.create(
        fk_alerta=instance.fk_alerta,
        fk_legajo=instance.fk_legajo,
        observaciones=instance.observaciones,
        creada_por=instance.creada_por,
    )
    registro.save()


