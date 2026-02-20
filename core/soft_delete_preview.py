"""UI-oriented preview helpers for soft-delete and restore cascades."""

from core.soft_delete_cascade import (
    build_delete_plan,
    build_restore_plan,
    summarize_plan,
)


def build_delete_preview(instance, *, sample_limit=5):
    """Preview of what will be affected by a soft-delete cascade."""
    plan = build_delete_plan(instance)
    data = summarize_plan(plan, sample_limit=sample_limit)
    data["operacion"] = "delete"
    return data


def build_restore_preview(instance, *, sample_limit=5):
    """Preview of what will be affected by a restore cascade."""
    plan = build_restore_plan(instance)
    data = summarize_plan(plan, sample_limit=sample_limit)
    data["operacion"] = "restore"
    return data
