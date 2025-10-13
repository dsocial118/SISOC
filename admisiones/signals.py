from django.db.models.signals import pre_save
from django.dispatch import receiver
from admisiones.models.admisiones import Admision, AdmisionHistorial
from config.middlewares.threadlocals import get_current_user


@receiver(pre_save, sender=Admision)
def guardar_historial_admision(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        previo = Admision.objects.get(pk=instance.pk)
    except Admision.DoesNotExist:
        return

    usuario = get_current_user()
    campos_a_trackear = [
        "modificado",
        "enviado_legales",
        "estado_legales",
        "observaciones",
        "intervencion_juridicos",
        "rechazo_juridicos_motivo",
        "dictamen_motivo",
        "informe_sga",
        "numero_convenio",
        "archivo_convenio",
        "enviada_a_archivo",
        "complementario_solicitado",
    ]

    for campo in campos_a_trackear:
        valor_anterior = getattr(previo, campo)
        valor_nuevo = getattr(instance, campo)

        field = sender._meta.get_field(campo)
        if field.choices:
            if valor_anterior is not None:
                valor_anterior = getattr(previo, f"get_{campo}_display")()
            if valor_nuevo is not None:
                valor_nuevo = getattr(instance, f"get_{campo}_display")()

        if valor_anterior != valor_nuevo:
            verbose_name = field.verbose_name.title()
            AdmisionHistorial.objects.create(
                admision=instance,
                campo=verbose_name,
                valor_anterior=valor_anterior,
                valor_nuevo=valor_nuevo,
                usuario=usuario,
            )
