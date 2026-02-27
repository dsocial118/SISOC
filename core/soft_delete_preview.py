"""Compatibility wrapper for legacy imports of soft-delete preview."""

from core.soft_delete.preview import build_delete_preview, build_restore_preview

__all__ = ["build_delete_preview", "build_restore_preview"]
