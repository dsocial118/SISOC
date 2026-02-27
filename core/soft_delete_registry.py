"""Compatibility wrapper for legacy imports of soft-delete registry."""

from core.soft_delete.registry import (
    SOFT_DELETE_MODEL_KEYS,
    get_soft_delete_model_choices,
    iter_soft_delete_models,
)

__all__ = [
    "SOFT_DELETE_MODEL_KEYS",
    "iter_soft_delete_models",
    "get_soft_delete_model_choices",
]
