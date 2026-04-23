"""Helpers for syncing operational state during soft-delete flows."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from django.apps import apps


_UNSET = object()


def build_soft_delete_operational_updates(model) -> dict[str, Any]:
    """Return operational field updates that should accompany a soft delete."""
    explicit_updates = getattr(model, "SOFT_DELETE_OPERATIONAL_UPDATES", None)
    return dict(explicit_updates or {})


def build_soft_restore_operational_updates(model) -> dict[str, Any]:
    """Return operational field updates that should accompany a restore."""
    explicit_updates = getattr(model, "SOFT_RESTORE_OPERATIONAL_UPDATES", None)
    return dict(explicit_updates or {})


@lru_cache(maxsize=1)
def _get_backfill_side_effect_handlers():
    from VAT.cache_utils import invalidate_planes_centro_cache_on_soft_delete
    from core.cache_utils import invalidate_cache_on_soft_delete_events

    return (
        invalidate_cache_on_soft_delete_events,
        invalidate_planes_centro_cache_on_soft_delete,
    )


def sync_soft_delete_instance_state(
    instance,
    *,
    deleted_at=_UNSET,
    deleted_by=_UNSET,
    operational_updates=None,
) -> None:
    """Mirror soft-delete state on an in-memory instance."""
    if operational_updates is None:
        operational_updates = {}

    if deleted_at is not _UNSET:
        instance.deleted_at = deleted_at
    if deleted_by is not _UNSET:
        instance.deleted_by = deleted_by
    for field_name, value in operational_updates.items():
        setattr(instance, field_name, value)


def run_soft_delete_backfill_side_effects(instance) -> None:
    """Run safe soft-delete side effects for backfilled legacy rows."""
    sender = instance.__class__
    for handler in _get_backfill_side_effect_handlers():
        handler(
            sender=sender,
            instance=instance,
            user=None,
            cascade=False,
            root=instance,
        )


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
