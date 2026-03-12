"""
Señales para crear entradas de auditoría adicionales asociadas a comedores y
organizaciones.
"""

import json

from django.db import OperationalError, ProgrammingError, transaction
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from auditlog.models import LogEntry
from admisiones.models.admisiones import Admision
from centrodeinfancia.models import (
    CentroDeInfancia,
    FormularioCDI,
    IntervencionCentroInfancia,
    NominaCentroInfancia,
)
from comedores.models import Comedor, ImagenComedor, Referente
from audittrail.context import get_audit_context
from audittrail.models import AuditEntryMeta
from config.middlewares.threadlocals import get_current_user
from core.soft_delete.signals import post_soft_delete
from intervenciones.models.intervenciones import Intervencion
from organizaciones.models import Aval, Firmante, Organizacion
from relevamientos.models import Relevamiento


AUDITTRAIL_EXTRA_BATCH_KEYS = (
    "audittrail_batch_key",
    "batch_id",
    "bulk_id",
    "job_id",
    "request_id",
    "correlation_id",
    "transaction_id",
    "cid",
)


def _normalize_additional_data(value):
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except Exception:  # noqa: BLE001
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _get_context_actor():
    actor = get_audit_context().get("actor")
    if actor and getattr(actor, "is_authenticated", False):
        return actor
    return None


def _get_actor():
    """
    Obtiene el usuario autenticado actual, si está disponible.
    """
    actor = _get_context_actor()
    if actor:
        return actor
    actor = get_current_user()
    if actor and getattr(actor, "is_authenticated", False):
        return actor
    return None


def _build_custom_signal_additional_data(default_source=None):
    """
    Propaga metadata de Fase 2 en logs custom (on_commit), para no perder batch/source.
    """
    context = get_audit_context()
    payload = {}

    source = (context.get("source") or "").strip() if isinstance(context, dict) else ""
    if not source and default_source:
        source = default_source
    if source:
        payload["audittrail_source"] = source

    batch_key = context.get("batch_key") if isinstance(context, dict) else None
    if batch_key not in (None, ""):
        payload["audittrail_batch_key"] = str(batch_key)

    extra = context.get("extra") if isinstance(context, dict) else None
    if isinstance(extra, dict) and extra:
        payload["audittrail_context"] = extra

    return payload or None


def _extract_meta_batch_key(entry, context_data, additional_data):
    context_batch_key = None
    if isinstance(context_data, dict):
        context_batch_key = context_data.get("batch_key")
    if context_batch_key not in (None, ""):
        return str(context_batch_key)

    custom_batch_key = additional_data.get("audittrail_batch_key")
    if custom_batch_key not in (None, ""):
        return str(custom_batch_key)

    cid = getattr(entry, "cid", None)
    if cid not in (None, ""):
        return f"cid:{cid}"

    for key in AUDITTRAIL_EXTRA_BATCH_KEYS:
        value = additional_data.get(key)
        if value not in (None, ""):
            return f"{key}:{value}"
    return ""


def _extract_meta_source(entry, context_data, additional_data):
    context_source = ""
    if isinstance(context_data, dict):
        context_source = str(context_data.get("source") or "").strip()
    if context_source:
        return context_source

    source = str(additional_data.get("audittrail_source") or "").strip()
    if source:
        return source

    if getattr(entry, "cid", None):
        return "http"
    if getattr(entry, "actor", None) or getattr(entry, "actor_id", None):
        return "http"
    return "system"


def _actor_snapshot_data(actor):
    if not actor or not getattr(actor, "is_authenticated", False):
        return {
            "username": "",
            "full_name": "",
            "display": "",
        }

    username = ""
    if hasattr(actor, "get_username"):
        try:
            username = str(actor.get_username() or "").strip()
        except Exception:  # noqa: BLE001
            username = ""
    if not username:
        username = str(getattr(actor, "username", "") or "").strip()

    first_name = str(getattr(actor, "first_name", "") or "").strip()
    last_name = str(getattr(actor, "last_name", "") or "").strip()
    full_name = " ".join(part for part in [first_name, last_name] if part).strip()

    display = username or full_name
    return {
        "username": username,
        "full_name": full_name,
        "display": display,
    }


def _build_audit_entry_meta_defaults(entry):
    """
    Construye metadata persistida Fase 2 a partir de LogEntry + contexto thread-local.
    """
    context_data = get_audit_context()
    additional_data = _normalize_additional_data(
        getattr(entry, "additional_data", None)
    )
    actor = getattr(entry, "actor", None) or _get_context_actor()
    actor_snapshot = _actor_snapshot_data(actor)
    batch_key = _extract_meta_batch_key(entry, context_data, additional_data)
    source = _extract_meta_source(entry, context_data, additional_data)

    extra = {}
    if isinstance(context_data, dict):
        context_extra = context_data.get("extra")
        if isinstance(context_extra, dict) and context_extra:
            extra["context"] = context_extra
    if additional_data.get("audittrail_context"):
        extra["custom_signal_context"] = additional_data.get("audittrail_context")
    if getattr(entry, "cid", None):
        extra["cid"] = str(entry.cid)

    return {
        "actor_username_snapshot": actor_snapshot["username"],
        "actor_full_name_snapshot": actor_snapshot["full_name"],
        "actor_display_snapshot": actor_snapshot["display"],
        "source": source,
        "batch_key": batch_key,
        "extra": extra,
    }


def _log_comedor_event(comedor: Comedor, changes: dict, action: int):
    """
    Genera una entrada de auditoría para un comedor con los cambios provistos.
    """
    if not comedor or not changes:
        return

    actor = _get_actor()
    additional_data = _build_custom_signal_additional_data()

    def _create_log():
        kwargs = {
            "action": action,
            "changes": changes,
            "actor": actor,
        }
        if additional_data and hasattr(LogEntry, "additional_data"):
            kwargs["additional_data"] = additional_data
        LogEntry.objects.log_create(comedor, **kwargs)

    transaction.on_commit(_create_log)


def _log_centro_infancia_event(
    centro: CentroDeInfancia,
    changes: dict,
    action: int,
):
    """
    Genera una entrada de auditoría para un centro de infancia con los cambios provistos.
    """
    if not centro or not changes:
        return

    actor = _get_actor()
    additional_data = _build_custom_signal_additional_data()

    def _create_log():
        kwargs = {
            "action": action,
            "changes": changes,
            "actor": actor,
        }
        if additional_data and hasattr(LogEntry, "additional_data"):
            kwargs["additional_data"] = additional_data
        LogEntry.objects.log_create(centro, **kwargs)

    transaction.on_commit(_create_log)


def _log_organizacion_event(organizacion: Organizacion, changes: dict, action: int):
    """
    Genera una entrada de auditoría para una organización con los cambios provistos.
    """
    if not organizacion or not changes:
        return

    actor = _get_actor()
    additional_data = _build_custom_signal_additional_data()

    def _create_log():
        kwargs = {
            "action": action,
            "changes": changes,
            "actor": actor,
        }
        if additional_data and hasattr(LogEntry, "additional_data"):
            kwargs["additional_data"] = additional_data
        LogEntry.objects.log_create(organizacion, **kwargs)

    transaction.on_commit(_create_log)


def _mark_delete_event_logged(instance) -> bool:
    """
    Evita registrar dos veces el mismo delete cuando conviven señales soft/hard delete.
    """
    marker_attr = "_audittrail_delete_logged"  # pylint: disable=protected-access
    if getattr(instance, marker_attr, False):
        return True
    setattr(instance, marker_attr, True)
    return False


def _log_related_organizacion_delete(instance, label: str):
    """
    Registra eliminación de una entidad relacionada a organización.
    """
    organizacion = getattr(instance, "organizacion", None)
    if not organizacion or _mark_delete_event_logged(instance):
        return
    _log_organizacion_event(
        organizacion,
        {label: [str(instance), "Eliminado"]},
        LogEntry.Action.DELETE,
    )


@receiver(post_save, sender=LogEntry)
def ensure_audit_entry_meta(sender, instance: LogEntry, created: bool, **kwargs):
    """
    Persiste metadata de Fase 2 para cualquier evento de django-auditlog.
    """
    if not created:
        return

    defaults = _build_audit_entry_meta_defaults(instance)
    try:
        AuditEntryMeta.objects.update_or_create(
            log_entry=instance,
            defaults=defaults,
        )
    except (OperationalError, ProgrammingError):
        # Permite bootstrapping previo a migrar audittrail (fase 2).
        return


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
def log_intervencion_creation(sender, instance: Intervencion, created: bool, **kwargs):
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


@receiver(post_save, sender=NominaCentroInfancia)
def log_nomina_centro_infancia_creation(
    sender,
    instance: NominaCentroInfancia,
    created: bool,
    **kwargs,
):
    """
    Registra altas de nómina vinculadas a un centro de infancia.
    """
    if not created or not instance.centro:
        return

    description = f"Nómina #{instance.pk}"
    if instance.ciudadano_id:
        description = f"{description} - {instance.ciudadano}"

    _log_centro_infancia_event(
        instance.centro,
        {"Nómina": [None, description]},
        LogEntry.Action.CREATE,
    )


@receiver(post_save, sender=IntervencionCentroInfancia)
def log_intervencion_centro_infancia_creation(
    sender,
    instance: IntervencionCentroInfancia,
    created: bool,
    **kwargs,
):
    """
    Registra altas de intervenciones vinculadas a un centro de infancia.
    """
    if not created or not instance.centro:
        return

    tipo = getattr(instance, "tipo_intervencion", None)
    description = f"Intervención #{instance.pk}"
    if tipo:
        description = f"{description} - {tipo}"

    _log_centro_infancia_event(
        instance.centro,
        {"Intervención": [None, description]},
        LogEntry.Action.CREATE,
    )


@receiver(post_save, sender=FormularioCDI)
def log_formulario_cdi_creation(sender, instance: FormularioCDI, created: bool, **kwargs):
    """
    Registra altas de formularios CDI vinculadas a un centro de infancia.
    """
    if not created or not instance.centro:
        return

    fecha = None
    if getattr(instance, "survey_date", None):
        fecha = instance.survey_date.strftime("%Y-%m-%d")

    description = f"Formulario CDI #{instance.pk}"
    if fecha:
        description = f"{description} - {fecha}"

    _log_centro_infancia_event(
        instance.centro,
        {"Formulario CDI": [None, description]},
        LogEntry.Action.CREATE,
    )


@receiver(post_save, sender=Relevamiento)
def log_relevamiento_creation(sender, instance: Relevamiento, created: bool, **kwargs):
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

    previous = getattr(
        instance, "_previous_state", None
    )  # pylint: disable=protected-access
    changes = {}

    if previous:
        for field_name in REFERENTE_FIELDS:
            old = getattr(previous, field_name, None)
            new = getattr(instance, field_name, None)
            if old != new:
                verbose = sender._meta.get_field(
                    field_name
                ).verbose_name  # pylint: disable=protected-access
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
def log_imagen_comedor_change(sender, instance: ImagenComedor, created: bool, **kwargs):
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

    previous = getattr(
        instance, "_previous_imagen", None
    )  # pylint: disable=protected-access
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


@receiver(pre_save, sender=Firmante)
def cache_firmante_state(sender, instance: Firmante, **kwargs):
    """
    Guarda el estado previo del firmante para detectar cambios.
    """
    if not instance.pk:
        return
    try:
        instance._previous_state = sender.objects.select_related(  # type: ignore[attr-defined]  # pylint: disable=protected-access
            "rol", "organizacion"
        ).get(
            pk=instance.pk
        )
    except sender.DoesNotExist:
        instance._previous_state = None  # type: ignore[attr-defined]  # pylint: disable=protected-access


@receiver(post_save, sender=Firmante)
def log_firmante_changes(sender, instance: Firmante, created: bool, **kwargs):
    """
    Registra creación y cambios de firmantes asociados a una organización.
    """
    if not instance.organizacion:
        return

    if created:
        descripcion = str(instance)
        _log_organizacion_event(
            instance.organizacion,
            {"Firmante": [None, descripcion]},
            LogEntry.Action.CREATE,
        )
        return

    previous = getattr(
        instance, "_previous_state", None
    )  # pylint: disable=protected-access
    changes = {}

    if previous:
        if previous.nombre != instance.nombre:
            changes["Firmante: Nombre"] = [previous.nombre, instance.nombre]
        if previous.cuit != instance.cuit:
            changes["Firmante: CUIT"] = [previous.cuit, instance.cuit]
        if previous.rol_id != instance.rol_id:
            changes["Firmante: Rol"] = [
                str(previous.rol) if previous.rol else None,
                str(instance.rol) if instance.rol else None,
            ]

    if hasattr(instance, "_previous_state"):  # pylint: disable=protected-access
        delattr(instance, "_previous_state")  # pylint: disable=protected-access

    if changes:
        _log_organizacion_event(instance.organizacion, changes, LogEntry.Action.UPDATE)


@receiver(pre_save, sender=Aval)
def cache_aval_state(sender, instance: Aval, **kwargs):
    """
    Guarda el estado previo del aval para detectar cambios.
    """
    if not instance.pk:
        return
    try:
        instance._previous_state = sender.objects.select_related(  # type: ignore[attr-defined]  # pylint: disable=protected-access
            "organizacion"
        ).get(
            pk=instance.pk
        )
    except sender.DoesNotExist:
        instance._previous_state = None  # type: ignore[attr-defined]  # pylint: disable=protected-access


@receiver(post_save, sender=Aval)
def log_aval_changes(sender, instance: Aval, created: bool, **kwargs):
    """
    Registra creación y cambios de avales asociados a una organización.
    """
    if not instance.organizacion:
        return

    if created:
        _log_organizacion_event(
            instance.organizacion,
            {"Aval": [None, str(instance)]},
            LogEntry.Action.CREATE,
        )
        return

    previous = getattr(
        instance, "_previous_state", None
    )  # pylint: disable=protected-access
    changes = {}

    if previous:
        if previous.nombre != instance.nombre:
            changes["Aval: Nombre"] = [previous.nombre, instance.nombre]
        if previous.cuit != instance.cuit:
            changes["Aval: CUIT"] = [previous.cuit, instance.cuit]

    if hasattr(instance, "_previous_state"):  # pylint: disable=protected-access
        delattr(instance, "_previous_state")  # pylint: disable=protected-access

    if changes:
        _log_organizacion_event(instance.organizacion, changes, LogEntry.Action.UPDATE)


@receiver(post_soft_delete, sender=Firmante)
@receiver(post_delete, sender=Firmante)
def log_firmante_delete(sender, instance: Firmante, **kwargs):
    """
    Registra bajas (soft/hard) de firmantes sin duplicar eventos.
    """
    _log_related_organizacion_delete(instance, "Firmante")


@receiver(post_soft_delete, sender=Aval)
@receiver(post_delete, sender=Aval)
def log_aval_delete(sender, instance: Aval, **kwargs):
    """
    Registra bajas (soft/hard) de avales sin duplicar eventos.
    """
    _log_related_organizacion_delete(instance, "Aval")
