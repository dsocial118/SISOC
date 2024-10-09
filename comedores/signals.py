from django.db.models.signals import post_save
from django.dispatch import receiver
from comedores.models import Relevamiento
from comedores.services.relevamiento_service import RelevamientoService


@receiver(post_save, sender=Relevamiento)
def post_save_mi_modelo(sender, instance, created, **kwargs):
    if created:
        RelevamientoService.send_to_gestionar(instance)
