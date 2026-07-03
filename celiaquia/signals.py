import logging

from django.db import transaction
from django.db.models import F, Q
from django.db.models.signals import pre_save
from django.dispatch import receiver

from config.middlewares.threadlocals import get_current_user
from core.soft_delete.signals import post_restore, post_soft_delete
from .models import (
    CupoMovimiento,
    EstadoCupo,
    Expediente,
    ExpedienteEstadoHistorial,
    ExpedienteCiudadano,
    HistorialCupo,
    ProvinciaCupo,
    TipoMovimientoCupo,
)
from .services.comentarios_service import ComentariosService

logger = logging.getLogger("django")


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


@receiver(post_restore, sender=Expediente)
def resolver_conflictos_ciudadanos_tras_restauracion(sender, instance, user, **kwargs):
    """
    Al restaurar un Expediente, re-elimina lógicamente los legajos cuyo ciudadano
    ya tiene otro legajo en un estado que no permite duplicación o está dentro del programa.

    Evita que un ciudadano quede vivo en dos expedientes simultáneamente cuando
    el Expediente fue eliminado y restaurado después de que ese ciudadano fue
    importado en otro expediente.
    """
    from celiaquia.services.importacion_service.impl import (
        REVISIONES_BLOQUEAN_NUEVO_EXPEDIENTE,
    )  # pylint: disable=import-outside-toplevel

    legajos_restaurados = ExpedienteCiudadano.objects.filter(expediente=instance)
    ciudadanos_ids = list(legajos_restaurados.values_list("ciudadano_id", flat=True))
    if not ciudadanos_ids:
        return

    ciudadanos_en_conflicto = set(
        ExpedienteCiudadano.objects.filter(ciudadano_id__in=ciudadanos_ids)
        .exclude(expediente=instance)
        .filter(
            Q(estado_cupo=EstadoCupo.DENTRO)
            | Q(revision_tecnico__in=REVISIONES_BLOQUEAN_NUEVO_EXPEDIENTE)
        )
        .values_list("ciudadano_id", flat=True)
    )

    if not ciudadanos_en_conflicto:
        return

    legajos_conflictivos = legajos_restaurados.filter(
        ciudadano_id__in=ciudadanos_en_conflicto
    )
    count = legajos_conflictivos.count()
    for legajo in legajos_conflictivos:
        legajo.delete(user=user, cascade=False)

    logger.warning(
        "Restauración de Expediente %s: %s legajo(s) re-eliminado(s) por conflicto "
        "con ciudadano(s) activo(s) en otro expediente.",
        instance.pk,
        count,
    )


def _ajustar_usados_por_ciclo_vida_legajo(legajo, *, delta, tipo, motivo, user=None):
    """Mantiene ``ProvinciaCupo.usados`` sincronizado cuando un titular con cupo
    entra o sale del universo vivo por soft-delete/restore.

    Un titular ocupa cupo si ``estado_cupo=DENTRO`` y su rol no es responsable
    puro (los responsables no consumen cupo). Al soft-borrarlo se descuenta
    ``usados`` (delta=-1) y al restaurarlo se vuelve a contar (delta=+1). Antes,
    soft-borrar un titular dejaba ``usados`` inflado y descuadraba el cupo.
    """
    from ciudadanos.models import Ciudadano  # pylint: disable=import-outside-toplevel

    with transaction.atomic():
        if legajo.estado_cupo != EstadoCupo.DENTRO:
            return
        if ExpedienteCiudadano.es_rol_responsable_puro(legajo.rol):
            return

        provincia_id = (
            Ciudadano.all_objects.filter(pk=legajo.ciudadano_id)
            .values_list("provincia_id", flat=True)
            .first()
        )
        if not provincia_id:
            return
        try:
            pc = (
                ProvinciaCupo.objects.select_for_update()
                .only("id", "usados", "total_asignado", "provincia_id")
                .get(provincia_id=provincia_id)
            )
        except ProvinciaCupo.DoesNotExist:
            return

        if delta < 0:
            if int(pc.usados or 0) <= 0:
                return
            cambiado = ProvinciaCupo.objects.filter(pk=pc.pk).update(
                usados=F("usados") - 1
            )
        else:
            disponibles = int(pc.total_asignado or 0) - int(pc.usados or 0)
            if disponibles <= 0:
                logger.warning(
                    "Cupo restore sin disponibles: legajo=%s provincia=%s",
                    legajo.pk,
                    provincia_id,
                )
                ExpedienteCiudadano.all_objects.filter(pk=legajo.pk).update(
                    estado_cupo=EstadoCupo.FUERA,
                    es_titular_activo=False,
                )
                return
            cambiado = ProvinciaCupo.objects.filter(pk=pc.pk).update(
                usados=F("usados") + 1
            )
        if not cambiado:
            return

        motivo_auditoria = motivo[:255]
        HistorialCupo.objects.create(
            legajo=legajo,
            estado_cupo_anterior=EstadoCupo.DENTRO,
            estado_cupo_nuevo=EstadoCupo.DENTRO,
            es_titular_activo_anterior=legajo.es_titular_activo,
            es_titular_activo_nuevo=legajo.es_titular_activo,
            tipo_movimiento=tipo,
            usuario=user,
            motivo=motivo_auditoria,
        )
        CupoMovimiento.objects.create(
            provincia_id=provincia_id,
            expediente_id=legajo.expediente_id,
            legajo=legajo,
            tipo=tipo,
            delta=delta,
            motivo=motivo_auditoria,
            usuario=user,
        )
        logger.info(
            "Cupo %s (%s): legajo=%s provincia=%s",
            tipo,
            motivo,
            legajo.pk,
            provincia_id,
        )


@receiver(post_soft_delete, sender=ExpedienteCiudadano)
def liberar_cupo_al_eliminar_legajo(sender, instance, user=None, **kwargs):
    """Libera el cupo al soft-borrar un titular (estado_cupo=DENTRO).

    Evita que ``ProvinciaCupo.usados`` quede inflado cuando se elimina (o se
    elimina en cascada por su expediente) un legajo que ocupaba cupo.
    """
    _ajustar_usados_por_ciclo_vida_legajo(
        instance,
        delta=-1,
        tipo=TipoMovimientoCupo.BAJA,
        motivo="Baja de cupo por eliminación de legajo",
        user=user,
    )


@receiver(post_restore, sender=ExpedienteCiudadano)
def reservar_cupo_al_restaurar_legajo(sender, instance, user=None, **kwargs):
    """Vuelve a contar el cupo al restaurar un titular que estaba DENTRO."""
    _ajustar_usados_por_ciclo_vida_legajo(
        instance,
        delta=1,
        tipo=TipoMovimientoCupo.ALTA,
        motivo="Alta de cupo por restauración de legajo",
        user=user,
    )
