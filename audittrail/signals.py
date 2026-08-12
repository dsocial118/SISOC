"""
Señales para crear entradas de auditoría adicionales asociadas a comedores y
organizaciones.
"""

import json

from django.db import OperationalError, ProgrammingError
from django.db.models.signals import post_save
from django.dispatch import receiver

from auditlog.models import LogEntry
from audittrail.context import get_audit_context
from audittrail.models import AuditEntryMeta


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
    Construye metadatos persistida Fase 2 a partir de LogEntry + contexto thread-local.
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


@receiver(post_save, sender=LogEntry)
def ensure_audit_entry_meta(sender, instance: LogEntry, created: bool, **kwargs):
    """
    Persiste metadatos de Fase 2 para cualquier evento de django-auditlog.
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
