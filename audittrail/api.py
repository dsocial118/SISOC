"""Contrato público para registrar eventos de auditoría de dominios."""

from __future__ import annotations

from typing import Any

from django.db import transaction

from auditlog.models import LogEntry

from audittrail.context import get_audit_context
from config.middlewares.threadlocals import get_current_user


ACTION_CREATE = LogEntry.Action.CREATE
ACTION_UPDATE = LogEntry.Action.UPDATE
ACTION_DELETE = LogEntry.Action.DELETE


def _actor_actual():
    context = get_audit_context()
    actor = context.get("actor") if isinstance(context, dict) else None
    if actor and getattr(actor, "is_authenticated", False):
        return actor
    actor = get_current_user()
    return actor if actor and getattr(actor, "is_authenticated", False) else None


def _additional_data() -> dict[str, Any] | None:
    context = get_audit_context()
    if not isinstance(context, dict):
        return None

    payload: dict[str, Any] = {}
    source = str(context.get("source") or "").strip()
    if source:
        payload["audittrail_source"] = source
    batch_key = context.get("batch_key")
    if batch_key not in (None, ""):
        payload["audittrail_batch_key"] = str(batch_key)
    extra = context.get("extra")
    if isinstance(extra, dict) and extra:
        payload["audittrail_context"] = extra
    return payload or None


def registrar_evento(
    objeto, cambios: dict[str, Any], accion: int = ACTION_CREATE
) -> None:
    """Registra un evento después del commit sin conocer el modelo del dominio."""

    if not objeto or not cambios:
        return

    actor = _actor_actual()
    additional_data = _additional_data()

    def _create_log():
        kwargs = {"action": accion, "changes": cambios, "actor": actor}
        if additional_data and hasattr(LogEntry, "additional_data"):
            kwargs["additional_data"] = additional_data
        LogEntry.objects.log_create(objeto, **kwargs)

    transaction.on_commit(_create_log)
