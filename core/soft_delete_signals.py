"""Compatibility wrapper for legacy imports of soft-delete signals."""

from core.soft_delete.signals import post_restore, post_soft_delete

__all__ = ["post_soft_delete", "post_restore"]
