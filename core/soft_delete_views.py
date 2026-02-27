"""Compatibility wrapper for legacy imports of soft-delete view helpers."""

from core.soft_delete.view_helpers import (
    SoftDeleteDeleteViewMixin,
    SuperAdminRequiredMixin,
    build_preview,
    delete_with_preview_response,
    is_soft_deletable_instance,
    restore_with_preview_response,
)

__all__ = [
    "SuperAdminRequiredMixin",
    "SoftDeleteDeleteViewMixin",
    "is_soft_deletable_instance",
    "build_preview",
    "delete_with_preview_response",
    "restore_with_preview_response",
]
