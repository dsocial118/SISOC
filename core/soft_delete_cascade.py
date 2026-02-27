"""Compatibility wrapper for legacy imports of soft-delete cascade."""

from core.soft_delete.cascade import (
    MODE_HARD,
    MODE_SOFT,
    OP_DELETE,
    OP_RESTORE,
    CascadeNode,
    CascadePlan,
    CascadeRelation,
    build_delete_plan,
    build_restore_plan,
    execute_delete_plan,
    execute_restore_plan,
    summarize_plan,
)

__all__ = [
    "MODE_HARD",
    "MODE_SOFT",
    "OP_DELETE",
    "OP_RESTORE",
    "CascadeNode",
    "CascadePlan",
    "CascadeRelation",
    "build_delete_plan",
    "build_restore_plan",
    "execute_delete_plan",
    "execute_restore_plan",
    "summarize_plan",
]
