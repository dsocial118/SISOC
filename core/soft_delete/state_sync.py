"""Helpers for syncing operational state during soft-delete flows."""

from __future__ import annotations

from typing import Any

from django.apps import apps
from django.core.exceptions import FieldDoesNotExist
from django.utils import timezone


def build_soft_delete_operational_updates(model) -> dict[str, Any]:
    """Return operational field updates that should accompany a soft delete."""
    updates: dict[str, Any] = {}

    explicit_updates = getattr(model, "SOFT_DELETE_OPERATIONAL_UPDATES", None)
    if explicit_updates is not None:
        updates.update(explicit_updates)

    try:
        model._meta.get_field("activo")  # noqa: SLF001
    except FieldDoesNotExist:
        pass
    else:
        updates.setdefault("activo", False)

    return updates


def sync_soft_delete_instance_state(
    instance,
    *,
    deleted_at=None,
    deleted_by=None,
    operational_updates=None,
) -> None:
    """Mirror soft-delete state on an in-memory instance."""
    if deleted_at is None:
        deleted_at = timezone.now()
    if operational_updates is None:
        operational_updates = {}

    instance.deleted_at = deleted_at
    instance.deleted_by = deleted_by
    for field_name, value in operational_updates.items():
        setattr(instance, field_name, value)


def is_soft_delete_model(model) -> bool:
    """Return whether the model exposes the soft-delete contract."""
    return (
        hasattr(model, "deleted_at")
        and hasattr(model, "all_objects")
        and hasattr(model, "restore")
    )


def iter_soft_delete_models_with_operational_updates(
    *, app_label=None, model_name=None
):
    """Yield soft-delete models that define effective operational updates."""
    for current_model in apps.get_models():
        if app_label is not None and current_model._meta.app_label != app_label:
            continue
        if (
            model_name is not None
            and current_model.__name__.lower() != model_name.lower()
        ):
            continue
        if not is_soft_delete_model(current_model):
            continue

        updates = build_soft_delete_operational_updates(current_model)
        if updates:
            yield current_model, updates


def get_soft_deleted_rows_pending_state_sync(model, updates):
    """Return deleted rows whose operational state does not match the expected one."""
    return model.all_objects.filter(deleted_at__isnull=False).exclude(**updates)
