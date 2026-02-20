"""
Utilidades para gestión de cache con invalidación automática.

Este módulo proporciona funciones para invalidar cache cuando se actualizan los datos relacionados.
"""

import logging

from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from core.soft_delete_signals import post_soft_delete, post_restore

logger = logging.getLogger("django")


def invalidate_cache_keys(*cache_keys):
    """
    Invalida múltiples claves de cache.

    Args:
        *cache_keys: Claves de cache a invalidar
    """
    for key in cache_keys:
        cache.delete(key)


def invalidate_cache_pattern(pattern):
    """
    Invalida claves de cache que coincidan con un patrón.

    Args:
        pattern: Patrón de clave de cache (ej: "comedor_*")

    Note:
        Actualmente no implementado para backend locmem.
        Se implementará cuando se migre a Redis.
    """
    # Nota: Django cache no soporta wildcard deletion por defecto
    # Para implementación completa necesitaríamos usar Redis con scan
    # Por ahora, usaremos claves específicas
    logger.warning(f"Invalidación por patrón no implementada para el patrón: {pattern}")


# Funciones específicas para invalidar cache por modelo
def invalidate_comedor_cache(comedor_id=None):
    """Invalida cache relacionado con comedores."""
    keys_to_invalidate = [
        "contar_comedores_activos",
    ]

    if comedor_id:
        keys_to_invalidate.extend(
            [
                f"presupuestos_comedor_{comedor_id}",
                "valores_comida_map",  # Este cache depende de datos de comedores
            ]
        )

    invalidate_cache_keys(*keys_to_invalidate)


def invalidate_ciudadano_cache(ciudadano_id=None):
    """Invalida cache relacionado con ciudadanos."""
    keys_to_invalidate = [
        "organismos",
        "programas",
        "estados_derivacion",
    ]

    if ciudadano_id:
        keys_to_invalidate.extend(
            [
                f"dims_{ciudadano_id}",
                f"ciudadano_context_{ciudadano_id}",
                "dimensiones_hogar",
            ]
        )

    invalidate_cache_keys(*keys_to_invalidate)


def invalidate_dashboard_cache():
    """Invalida cache del dashboard."""
    keys_to_invalidate = [
        "contar_comedores_activos",
        "contar_relevamientos_activos",
        "contar_ciudadanos_activos",
        "contar_beneficiarios_activos",
        "contar_alertas_activas",
    ]

    invalidate_cache_keys(*keys_to_invalidate)


def invalidate_intervenciones_cache():
    """Invalida cache de intervenciones."""
    keys_to_invalidate = [
        "tipos_intervencion",
        "destinatarios",
    ]

    invalidate_cache_keys(*keys_to_invalidate)


def invalidate_territoriales_cache():
    """Invalida cache de territoriales (método legacy)."""
    keys_to_invalidate = [
        "territoriales_list",  # Legacy key
    ]

    invalidate_cache_keys(*keys_to_invalidate)


def invalidate_territoriales_cache_provincia(provincia_id=None):
    """Invalida cache territorial por provincia."""
    if provincia_id:
        cache_key = f"territoriales_provincia_{provincia_id}"
        cache.delete(cache_key)
        logger.info(f"Invalidado cache territorial para provincia {provincia_id}")
    else:
        # Invalidar todas las provincias
        from core.models import Provincia  # pylint: disable=import-outside-toplevel

        provincias = Provincia.objects.values_list("id", flat=True)
        for prov_id in provincias:
            cache.delete(f"territoriales_provincia_{prov_id}")
        logger.info("Invalidado cache territorial para todas las provincias")


def invalidate_centrodefamilia_cache(user_id=None):
    """Invalida cache relacionado con centro de familia."""
    if user_id:
        keys_to_invalidate = [
            f"is_referente_{user_id}",
            f"is_referente_grupo_{user_id}",
        ]
        invalidate_cache_keys(*keys_to_invalidate)


# Signals para invalidación automática
@receiver([post_save, post_delete], sender="comedores.Comedor")
def invalidate_comedor_cache_on_change(sender, instance, **kwargs):
    """Invalida cache cuando se modifica un comedor."""
    invalidate_comedor_cache(instance.id)
    invalidate_dashboard_cache()


@receiver([post_save, post_delete], sender="ciudadanos.Ciudadano")
def invalidate_ciudadano_cache_on_change(sender, instance, **kwargs):
    """Invalida cache cuando se modifica un ciudadano."""
    invalidate_ciudadano_cache(instance.id)
    invalidate_dashboard_cache()


@receiver([post_soft_delete, post_restore])
def invalidate_cache_on_soft_delete_events(sender, instance, **kwargs):
    """Invalida cache relevante cuando hay baja lógica o restauración."""
    label = instance._meta.label_lower
    if label == "comedores.comedor":
        invalidate_comedor_cache(instance.id)
        invalidate_dashboard_cache()
    elif label == "ciudadanos.ciudadano":
        invalidate_ciudadano_cache(instance.id)
        invalidate_dashboard_cache()


@receiver([post_save, post_delete], sender="intervenciones.TipoIntervencion")
def invalidate_tipo_intervencion_cache_on_change(sender, instance, **kwargs):
    """Invalida cache cuando se modifica un tipo de intervención."""
    invalidate_intervenciones_cache()


@receiver([post_save, post_delete], sender="intervenciones.TipoDestinatario")
def invalidate_destinatario_cache_on_change(sender, instance, **kwargs):
    """Invalida cache cuando se modifica un tipo de destinatario."""
    invalidate_intervenciones_cache()


# Señales específicas para invalidación de cache
@receiver([post_save, post_delete], sender="comedores.ValorComida")
def invalidate_valor_comida_cache_on_change(sender, **kwargs):
    """Invalida cache cuando cambian valores de comida."""
    invalidate_cache_keys("valores_comida_map")


@receiver([post_save, post_delete], sender="comedores.TerritorialCache")
def invalidate_territorial_cache_on_change(sender, instance, **kwargs):
    """Invalida cache cuando cambian datos de territoriales por provincia."""
    # Invalidar cache legacy
    invalidate_territoriales_cache()

    # Invalidar cache específico por provincia si existe
    if hasattr(instance, "provincia_id") and instance.provincia_id:
        invalidate_territoriales_cache_provincia(instance.provincia_id)
    else:
        # Fallback: invalidar todas las provincias
        invalidate_territoriales_cache_provincia()


# Funciones helper para uso en vistas
def get_or_set_cache_with_invalidation(
    cache_key, fetch_function, timeout, invalidation_keys=None
):
    """
    Wrapper para cache.get_or_set que registra claves para invalidación.

    Args:
        cache_key: Clave del cache
        fetch_function: Función para obtener datos si no están en cache
        timeout: Tiempo de vida del cache
        invalidation_keys: Claves adicionales a invalidar cuando se actualice este cache

    Returns:
        Valor del cache o resultado de fetch_function
    """
    value = cache.get(cache_key)
    if value is None:
        value = fetch_function()
        cache.set(cache_key, value, timeout)

        # Opcional: registrar claves relacionadas para invalidación futura
        if invalidation_keys:
            related_keys = cache.get("cache_relationships", {})
            for key in invalidation_keys:
                if key not in related_keys:
                    related_keys[key] = []
                related_keys[key].append(cache_key)
            cache.set("cache_relationships", related_keys, timeout * 2)

    return value
