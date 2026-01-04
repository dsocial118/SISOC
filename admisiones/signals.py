from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from admisiones.models.admisiones import (
    Admision,
    AdmisionHistorial,
    HistorialEstadosAdmision,
)
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


@receiver(pre_save, sender=Admision)
def cache_estado_admision(sender, instance, **kwargs):
    if not instance.pk:
        return
    prev_data = (
        Admision.objects.filter(pk=instance.pk)
        .values("estado_admision", "estado_legales", "enviado_legales")
        .first()
    )
    if prev_data:
        instance._prev_estado_admision = prev_data["estado_admision"]
        instance._prev_estado_legales = prev_data["estado_legales"]
        instance._prev_enviado_legales = prev_data["enviado_legales"]


@receiver(post_save, sender=Admision)
def guardar_historial_estado_admision(sender, instance, created, **kwargs):
    if created:
        # Crear registro inicial para nueva admisión
        usuario = get_current_user()
        def _crear_historial_inicial():
            HistorialEstadosAdmision.objects.create(
                admision=instance,
                estado_anterior=None,
                estado_nuevo=instance.estado_admision or "iniciada",
                usuario=usuario,
            )
        transaction.on_commit(_crear_historial_inicial)
        return
    
    usuario = get_current_user()
    
    # Trackear cambios en estado_admision (solo si no está enviado a legales)
    estado_anterior = getattr(instance, "_prev_estado_admision", None)
    if estado_anterior != instance.estado_admision and not instance.enviado_legales:
        def _crear_historial_admision():
            estado_anterior_display = dict(instance.ESTADOS_ADMISION).get(estado_anterior, estado_anterior) if estado_anterior else None
            estado_nuevo_display = dict(instance.ESTADOS_ADMISION).get(instance.estado_admision, instance.estado_admision)
            
            HistorialEstadosAdmision.objects.create(
                admision=instance,
                estado_anterior=estado_anterior_display,
                estado_nuevo=estado_nuevo_display,
                usuario=usuario,
            )
        transaction.on_commit(_crear_historial_admision)
    
    # Trackear cambios en estado_legales
    estado_legales_anterior = getattr(instance, "_prev_estado_legales", None)
    if estado_legales_anterior != instance.estado_legales:
        def _crear_historial_legales():
            estado_anterior_display = dict(instance.ESTADOS_LEGALES).get(estado_legales_anterior, estado_legales_anterior) if estado_legales_anterior else None
            estado_nuevo_display = dict(instance.ESTADOS_LEGALES).get(instance.estado_legales, instance.estado_legales) if instance.estado_legales else None
            
            HistorialEstadosAdmision.objects.create(
                admision=instance,
                estado_anterior=estado_anterior_display,
                estado_nuevo=estado_nuevo_display,
                usuario=usuario,
            )
        transaction.on_commit(_crear_historial_legales)
    
    # Caso especial: cuando se envía a legales por primera vez
    enviado_legales_anterior = getattr(instance, "_prev_enviado_legales", False)
    if not enviado_legales_anterior and instance.enviado_legales:
        def _crear_historial_envio_legales():
            estado_actual = dict(instance.ESTADOS_ADMISION).get(instance.estado_admision, instance.estado_admision)
            HistorialEstadosAdmision.objects.create(
                admision=instance,
                estado_anterior=estado_actual,
                estado_nuevo="Enviado a Legales",
                usuario=usuario,
            )
        transaction.on_commit(_crear_historial_envio_legales)
