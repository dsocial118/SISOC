from django.db import connections
from django.db.models.signals import post_migrate, post_save, pre_delete
from django.dispatch import receiver

from relevamientos.models import PrimerSeguimiento, Relevamiento
from relevamientos.tasks import (
    AsyncSendRelevamientoToGestionar,
    AsyncRemoveRelevamientoToGestionar,
    AsyncRemovePrimerSeguimientoToGestionar,
    build_relevamiento_payload,
)
from core.soft_delete.signals import post_soft_delete


@receiver(post_save, sender=Relevamiento)
def send_relevamiento_to_gestionar(sender, instance, created, **kwargs):
    if created:
        if getattr(instance, "_skip_gestionar_sync", False):
            return
        payload = build_relevamiento_payload(instance)
        AsyncSendRelevamientoToGestionar(instance.id, payload).start()


@receiver(post_save, sender=Relevamiento)
def update_comedor_geolocalizacion(sender, instance, created, **kwargs):
    """
    Actualiza la geolocalización del comedor cuando el relevamiento está finalizado
    y tiene datos de excepción con latitud/longitud. n
    """
    if instance.estado in ["Finalizado", "Finalizado/Excepciones"]:
        if instance.excepcion and instance.comedor:
            if instance.excepcion.latitud and instance.excepcion.longitud:
                comedor = instance.comedor
                comedor.latitud = instance.excepcion.latitud
                comedor.longitud = instance.excepcion.longitud
                comedor.save(update_fields=["latitud", "longitud"])


@receiver(pre_delete, sender=Relevamiento)
@receiver(post_soft_delete, sender=Relevamiento)
def remove_relevamiento_to_gestionar(sender, instance, **kwargs):
    AsyncRemoveRelevamientoToGestionar(instance.id).start()


@receiver(pre_delete, sender=PrimerSeguimiento)
def remove_primer_seguimiento_to_gestionar(sender, instance, **kwargs):
    if not instance.gestionar_id:
        return
    AsyncRemovePrimerSeguimientoToGestionar(
        instance.id, instance.gestionar_id, instance.id_relevamiento_id
    ).start()


@receiver(post_migrate)
def sembrar_motivos_excepcion_seguimiento(sender, **kwargs):
    """Garantiza el catalogo cerrado del acta de excepcion en todo entorno.

    Va por ``post_migrate`` y no por una migracion de datos porque los tests
    crean el schema con ``TEST={"MIGRATE": False}``: un ``RunPython`` nunca
    correria ahi y el catalogo quedaria vacio, rechazando todos los motivos.

    Django emite ``post_migrate`` para TODAS las apps en cada ``migrate``,
    incluso uno parcial (el entrypoint de produccion corre ``migrate auth``
    antes del ``migrate`` general). Si en ese momento la tabla del catalogo
    todavia no existe (relevamientos < 0016), consultarla rompe el comando y
    deja el contenedor en crash-loop. Por eso, igual que ``pwa/signals.py``,
    se verifica la tabla antes de sembrar.
    """
    if getattr(sender, "name", None) != "relevamientos":
        return

    from relevamientos.models import (  # pylint: disable=import-outside-toplevel
        MotivoExcepcionSeguimiento,
    )

    using = kwargs.get("using") or "default"
    connection = connections[using]
    table_name = MotivoExcepcionSeguimiento._meta.db_table
    if table_name not in connection.introspection.table_names():
        return

    for nombre in MotivoExcepcionSeguimiento.MOTIVOS_CANONICOS:
        MotivoExcepcionSeguimiento.objects.using(using).get_or_create(nombre=nombre)
