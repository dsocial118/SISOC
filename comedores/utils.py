"""Utility helpers for comedores app.

This module provides small reusable functions for common data
transformations and cache handling used across comedor services."""

from typing import Any, Optional, Type

from django.conf import settings
from django.core.cache import cache
from django.db.models import Model

from comedores.models import ValorComida


def get_object_by_filter(model: Type[Model], **kwargs):
    """Return the first object of ``model`` matching ``kwargs`` or ``None``."""
    return model.objects.filter(**kwargs).first()


def get_id_by_nombre(model: Type[Model], nombre: str):
    """Return the ``id`` of the instance whose ``nombre`` matches ``nombre``.

    Comparison is case-insensitive. Returns an empty string if not found.
    """
    obj = model.objects.filter(nombre__iexact=nombre).first()
    return obj.id if obj else ""


def normalize_field(valor: Optional[str], chars_to_remove: str) -> Optional[str]:
    """Remove any ``chars_to_remove`` from ``valor`` and normalize empty values."""
    if valor:
        for char in chars_to_remove:
            valor = valor.replace(char, "")
    return valor or None


def preload_valores_comida_cache() -> dict[str, Any]:
    """Load ``ValorComida`` values into cache and return the mapping."""
    valor_map = cache.get("valores_comida_map")
    if not valor_map:
        valores_comida = ValorComida.objects.filter(
            tipo__in=["desayuno", "almuerzo", "merienda", "cena"]
        ).values("tipo", "valor")
        valor_map = {item["tipo"].lower(): item["valor"] for item in valores_comida}
        cache.set("valores_comida_map", valor_map, settings.DEFAULT_CACHE_TIMEOUT)
    return valor_map
