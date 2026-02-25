"""Contexto thread-local para enriquecer eventos de auditoría."""

from contextlib import contextmanager
import threading

_audittrail_locals = threading.local()


def get_audit_context():
    """Devuelve el contexto de auditoría actual (thread-local)."""
    context = getattr(_audittrail_locals, "context", None)
    if not isinstance(context, dict):
        return {}
    return context.copy()


def set_audit_context(**kwargs):
    """
    Actualiza el contexto de auditoría del thread actual.

    Keys esperadas (todas opcionales):
    - actor
    - source
    - batch_key
    - extra (dict)
    """
    current = get_audit_context()
    for key, value in kwargs.items():
        if value is None:
            current.pop(key, None)
        else:
            current[key] = value
    _audittrail_locals.context = current
    return current.copy()


def clear_audit_context():
    """Limpia el contexto de auditoría del thread actual."""
    _audittrail_locals.context = {}


@contextmanager
def audit_context(*, actor=None, source=None, batch_key=None, extra=None):
    """
    Context manager para operaciones batch/scripts sin request HTTP.

    Ejemplo:
        with audit_context(source="management_command:fix_x", batch_key="fix-20260225"):
            ...
    """
    previous = get_audit_context()
    try:
        updates = {}
        if actor is not None:
            updates["actor"] = actor
        if source is not None:
            updates["source"] = source
        if batch_key is not None:
            updates["batch_key"] = str(batch_key)
        if extra is not None:
            updates["extra"] = dict(extra) if isinstance(extra, dict) else {"value": str(extra)}
        set_audit_context(**updates)
        yield get_audit_context()
    finally:
        _audittrail_locals.context = previous
