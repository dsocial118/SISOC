from django.core.cache import cache
from django.db import connection
from django.db.models import Sum

from comedores.models.relevamiento import Relevamiento
from comedores.models.comedor import Comedor, ValorComida


def table_exists(table_name):

    with connection.cursor() as cursor:
        cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
        return cursor.fetchone() is not None


CACHE_TIMEOUT = 300  # Tiempo en segundos (5 minutos)


def contar_comedores_activos():
    """Contar la cantidad de comedores activos."""
    cache_key = "contar_comedores_activos"
    cached_value = cache.get(cache_key)
    if cached_value is None:
        cached_value = Comedor.objects.count()
        cache.set(cache_key, cached_value, timeout=CACHE_TIMEOUT)
    return cached_value


def contar_relevamientos_activos():
    """Contar la cantidad de relevamientos activos."""
    cache_key = "contar_relevamientos_activos"
    cached_value = cache.get(cache_key)
    if cached_value is None:
        cached_value = Relevamiento.objects.count()
        cache.set(cache_key, cached_value, timeout=CACHE_TIMEOUT)
    return cached_value


def calcular_presupuesto_desayuno():
    """Calcular el presupuesto total para desayunos."""
    cache_key = "calcular_presupuesto_desayuno"
    cached_value = cache.get(cache_key)
    if cached_value is None:
        cached_value = (
            ValorComida.objects.filter(tipo="desayuno").aggregate(total=Sum("valor"))[
                "total"
            ]
            or 0
        )
        cache.set(cache_key, cached_value, timeout=CACHE_TIMEOUT)
    return cached_value


def calcular_presupuesto_merienda():
    """Calcular el presupuesto total para meriendas."""
    cache_key = "calcular_presupuesto_merienda"
    cached_value = cache.get(cache_key)
    if cached_value is None:
        cached_value = (
            ValorComida.objects.filter(tipo="merienda").aggregate(total=Sum("valor"))[
                "total"
            ]
            or 0
        )
        cache.set(cache_key, cached_value, timeout=CACHE_TIMEOUT)
    return cached_value


def calcular_presupuesto_comida():
    """Calcular el presupuesto total para comidas."""
    cache_key = "calcular_presupuesto_comida"
    cached_value = cache.get(cache_key)
    if cached_value is None:
        cached_value = (
            ValorComida.objects.filter(tipo="comida").aggregate(total=Sum("valor"))[
                "total"
            ]
            or 0
        )
        cache.set(cache_key, cached_value, timeout=CACHE_TIMEOUT)
    return cached_value
