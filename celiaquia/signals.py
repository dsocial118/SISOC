from django.db.models.signals import pre_save
from django.dispatch import receiver

from config.middlewares.threadlocals import get_current_user
from .models import Expediente, ExpedienteEstadoHistorial, ExpedienteCiudadano
from .services.comentarios_service import ComentariosService


@receiver(pre_save, sender=Expediente)
def registrar_historial_estado(sender, instance, **_):
    """Registra el historial cuando cambia el estado de un expediente."""
    if not instance.pk:
        return
    try:
        previous = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:  # pragma: no cover - race condition
        return
    if previous.estado_id != instance.estado_id:
        ExpedienteEstadoHistorial.objects.create(
            expediente=instance,
            estado_anterior=previous.estado,
            estado_nuevo=instance.estado,
            usuario=get_current_user(),
        )


@receiver(pre_save, sender=ExpedienteCiudadano)
def registrar_comentarios_automaticos(sender, instance, **_):
    """Registra comentarios automáticamente cuando cambian campos relevantes."""
    if not instance.pk:
        return

    try:
        previous = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    usuario = get_current_user()

    # Registrar cambio en motivo de subsanación
    if (
        previous.subsanacion_motivo != instance.subsanacion_motivo
        and instance.subsanacion_motivo
    ):
        ComentariosService.agregar_subsanacion_motivo(
            legajo=instance, motivo=instance.subsanacion_motivo, usuario=usuario
        )

    # Registrar cambio en comentario RENAPER
    if (
        previous.subsanacion_renaper_comentario
        != instance.subsanacion_renaper_comentario
        and instance.subsanacion_renaper_comentario
    ):
        ComentariosService.agregar_validacion_renaper(
            legajo=instance,
            comentario=instance.subsanacion_renaper_comentario,
            usuario=usuario,
        )

    # Registrar cambio en observación de cruce
    if (
        previous.observacion_cruce != instance.observacion_cruce
        and instance.observacion_cruce
    ):
        ComentariosService.agregar_cruce_sintys(
            legajo=instance, observacion=instance.observacion_cruce, usuario=usuario
        )

    # Registrar cambio en revisión técnica
    if previous.revision_tecnico != instance.revision_tecnico:
        estado_display = dict(instance._meta.get_field("revision_tecnico").choices)
        prev_estado = estado_display.get(
            previous.revision_tecnico, previous.revision_tecnico
        )
        new_estado = estado_display.get(
            instance.revision_tecnico, instance.revision_tecnico
        )
        comentario = f"Estado cambiado de {prev_estado} a {new_estado}"
        ComentariosService.agregar_validacion_tecnica(
            legajo=instance, comentario=comentario, usuario=usuario
        )
