"""Core soft-delete domain package."""

from .base import SoftDeleteManager, SoftDeleteModelMixin, SoftDeleteQuerySet

__all__ = [
    "SoftDeleteQuerySet",
    "SoftDeleteManager",
    "SoftDeleteModelMixin",
]
