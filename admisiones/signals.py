from django.db.models.signals import pre_save
from django.dispatch import receiver
from admisiones.models.admisiones import Admision, AdmisionHistorial
from .threadlocals import get_current_user


@receiver(pre_save, sender=Admision)
def guardar_historial_admision(sender, instance, **kwargs):
    if not instance.pk:
        return  # solo trackear cambios de objetos existentes

    try:
        previo = Admision.objects.get(pk=instance.pk)
    except Admision.DoesNotExist:
        return

    usuario = get_current_user()
    campos_a_trackear = ['modificado', 'enviado_legales', 'estado_legales', 'observaciones']

    for campo in campos_a_trackear:
        valor_anterior = getattr(previo, campo)
        valor_nuevo = getattr(instance, campo)

        if valor_anterior != valor_nuevo:
            verbose_name = sender._meta.get_field(campo).verbose_name.title()
            AdmisionHistorial.objects.create(
                admision=instance,
                campo=verbose_name,
                valor_anterior=valor_anterior,
                valor_nuevo=valor_nuevo,
                usuario=usuario
            )
