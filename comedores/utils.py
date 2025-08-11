"""Funciones auxiliares para la app de comedores.

Este módulo contiene utilidades reutilizables para transformaciones de datos
comunes y manejo de cache utilizadas por los servicios de comedores.
"""

from typing import Any, Optional, Type

from django.conf import settings
from django.core.cache import cache
from django.db.models import Model

from comedores.models import ValorComida


def get_object_by_filter(model: Type[Model], **kwargs):
    """Obtener el primer objeto de ``model`` que coincida con ``kwargs``."""
    return model.objects.filter(**kwargs).first()


def get_id_by_nombre(model: Type[Model], nombre: str):
    """Devolver el ``id`` de la instancia cuyo ``nombre`` coincide.

    La comparación no distingue mayúsculas de minúsculas. Retorna cadena vacía
    si no se encuentra coincidencia.
    """
    obj = model.objects.filter(nombre__iexact=nombre).first()
    return obj.id if obj else ""


def normalize_field(valor: Optional[str], chars_to_remove: str) -> Optional[str]:
    """Eliminar caracteres específicos de ``valor`` y normalizar vacíos."""
    if valor:
        for char in chars_to_remove:
            valor = valor.replace(char, "")
    return valor or None


def preload_valores_comida_cache() -> dict[str, Any]:
    """Cargar valores de ``ValorComida`` en cache y devolver el mapeo."""
    valor_map = cache.get("valores_comida_map")
    if not valor_map:
        valores_comida = ValorComida.objects.filter(
            tipo__in=["desayuno", "almuerzo", "merienda", "cena"]
        ).values("tipo", "valor")
        valor_map = {item["tipo"].lower(): item["valor"] for item in valores_comida}
        cache.set("valores_comida_map", valor_map, settings.DEFAULT_CACHE_TIMEOUT)
    return valor_map
