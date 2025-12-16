"""
Señales para crear entradas de auditoría adicionales asociadas a comedores.
"""

from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from auditlog.models import LogEntry
from admisiones.models.admisiones import Admision
from comedores.models import Comedor, ImagenComedor, Referente
from config.middlewares.threadlocals import get_current_user
from intervenciones.models.intervenciones import Intervencion
from relevamientos.models import Relevamiento


def _get_actor():
    """
    Obtiene el usuario autenticado actual, si está disponible.
    """
    actor = get_current_user()
    if actor and getattr(actor, "is_authenticated", False):
        return actor
    return None


def _log_comedor_event(comedor: Comedor, changes: dict, action: int):
    """
    Genera una entrada de auditoría para un comedor con los cambios provistos.
    """
    if not comedor or not changes:
        return

    actor = _get_actor()

    def _create_log():
        LogEntry.objects.log_create(
            comedor,
            action=action,
            changes=changes,
            actor=actor,
        )

    transaction.on_commit(_create_log)


@receiver(post_save, sender=Admision)
def log_admision_creation(sender, instance: Admision, created: bool, **kwargs):
    """
    Registra la creación de admisiones vinculadas a un comedor.
    """
    if not created or not instance.comedor:
        return

    estado = getattr(instance, "estado_mostrar", None)
    description = f"Admisión #{instance.pk}"
    if estado:
        description = f"{description} ({estado})"

    _log_comedor_event(
        instance.comedor,
        {"Admisión": [None, description]},
        LogEntry.Action.CREATE,
    )


@receiver(post_save, sender=Intervencion)
def log_intervencion_creation(
    sender, instance: Intervencion, created: bool, **kwargs
):
    """
    Registra la creación de intervenciones vinculadas a un comedor.
    """
    if not created or not instance.comedor:
        return

    tipo = getattr(instance, "tipo_intervencion", None)
    description = f"Intervención #{instance.pk}"
    if tipo:
        description = f"{description} - {tipo}"

    _log_comedor_event(
        instance.comedor,
        {"Intervención": [None, description]},
        LogEntry.Action.CREATE,
    )


@receiver(post_save, sender=Relevamiento)
def log_relevamiento_creation(
    sender, instance: Relevamiento, created: bool, **kwargs
):
    """
    Registra la creación de relevamientos vinculados a un comedor.
    """
    if not created or not instance.comedor:
        return

    fecha = None
    if getattr(instance, "fecha_visita", None):
        fecha = getattr(instance, "fecha_visita", None)
        if hasattr(fecha, "strftime"):
            fecha = fecha.strftime("%Y-%m-%d")
    description = f"Relevamiento #{instance.pk}"
    if fecha:
        description = f"{description} - {fecha}"

    _log_comedor_event(
        instance.comedor,
        {"Relevamiento": [None, description]},
        LogEntry.Action.CREATE,
    )


REFERENTE_FIELDS = ["nombre", "apellido", "mail", "celular", "documento", "funcion"]


@receiver(pre_save, sender=Referente)
def cache_referente_state(sender, instance: Referente, **kwargs):
    """
    Guarda el estado previo del referente para detectar cambios.
    """
    if not instance.pk:
        return
    try:
        instance._previous_state = sender.objects.get(pk=instance.pk)  # type: ignore[attr-defined]  # pylint: disable=protected-access
    except sender.DoesNotExist:
        instance._previous_state = None  # type: ignore[attr-defined]  # pylint: disable=protected-access


@receiver(post_save, sender=Referente)
def log_referente_update(sender, instance: Referente, created: bool, **kwargs):
    """
    Registra los cambios en datos del referente para cada comedor asociado.
    """
    if created:
        return

    previous = getattr(instance, "_previous_state", None)  # pylint: disable=protected-access
    changes = {}

    if previous:
        for field_name in REFERENTE_FIELDS:
            old = getattr(previous, field_name, None)
            new = getattr(instance, field_name, None)
            if old != new:
                verbose = sender._meta.get_field(field_name).verbose_name  # pylint: disable=protected-access
                changes[f"Referente: {verbose}"] = [old, new]

    # Limpiar referencia al estado previo para evitar fugas
    if hasattr(instance, "_previous_state"):  # pylint: disable=protected-access
        delattr(instance, "_previous_state")  # pylint: disable=protected-access

    if not changes:
        return

    for comedor in Comedor.objects.filter(referente=instance):
        _log_comedor_event(comedor, changes, LogEntry.Action.UPDATE)


@receiver(pre_save, sender=ImagenComedor)
def cache_imagen_comedor_state(sender, instance: ImagenComedor, **kwargs):
    """
    Almacena el estado previo de la imagen para comparar cambios.
    """
    if not instance.pk:
        return
    try:
        previous = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        previous = None

    if previous:
        instance._previous_imagen = {  # type: ignore[attr-defined]  # pylint: disable=protected-access
            "imagen": previous.imagen.name if previous.imagen else "",
            "comedor_id": previous.comedor_id,
        }


@receiver(post_save, sender=ImagenComedor)
def log_imagen_comedor_change(
    sender, instance: ImagenComedor, created: bool, **kwargs
):
    """
    Registra altas y modificaciones de imágenes asociadas a un comedor.
    """
    imagen_nombre = instance.imagen.name if instance.imagen else ""

    if created:
        _log_comedor_event(
            instance.comedor,
            {"Imagen": [None, imagen_nombre or "Imagen creada"]},
            LogEntry.Action.CREATE,
        )
        return

    previous = getattr(instance, "_previous_imagen", None)  # pylint: disable=protected-access
    changes = {}

    if previous:
        if previous.get("imagen") != imagen_nombre:
            changes["Imagen"] = [
                previous.get("imagen") or "Sin imagen",
                imagen_nombre or "Sin imagen",
            ]
        if previous.get("comedor_id") != instance.comedor_id:
            changes["Imagen: Comedor"] = [
                previous.get("comedor_id"),
                instance.comedor_id,
            ]

    if hasattr(instance, "_previous_imagen"):  # pylint: disable=protected-access
        delattr(instance, "_previous_imagen")  # pylint: disable=protected-access

    if changes:
        _log_comedor_event(instance.comedor, changes, LogEntry.Action.UPDATE)


@receiver(post_delete, sender=ImagenComedor)
def log_imagen_comedor_deletion(sender, instance: ImagenComedor, **kwargs):
    """
    Registra la eliminación de imágenes asociadas a un comedor.
    """
    imagen_nombre = instance.imagen.name if instance.imagen else "Imagen eliminada"
    _log_comedor_event(
        instance.comedor,
        {"Imagen": [imagen_nombre, "Eliminada"]},
        LogEntry.Action.DELETE,
    )
