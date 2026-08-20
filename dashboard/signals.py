"""Actualización de métricas del dashboard mediante contratos de dominio."""

from django.core.cache import cache

from comedores.api import registrar_observador_dashboard as observar_comedores
from dashboard.models import Dashboard
from dashboard.utils import (
    calcular_presupuesto_comida,
    calcular_presupuesto_desayuno,
    calcular_presupuesto_merienda,
    contar_comedores_activos,
    contar_relevamientos_activos,
    table_exists,
)
from relevamientos.api import registrar_observador_dashboard as observar_relevamientos


TABLES_REQUERIDAS = (
    "comedores_comedor",
    "relevamientos_relevamiento",
    "relevamientos_prestacion",
    "comedores_valorcomida",
)

DASHBOARD_CACHE_KEYS = (
    "contar_comedores_activos",
    "contar_relevamientos_activos",
    "calcular_presupuesto_desayuno",
    "calcular_presupuesto_merienda",
    "calcular_presupuesto_comida",
)


def _tablas_requeridas_existen():
    """Evita actualizar métricas mientras las migraciones aún no crearon sus tablas."""

    return all(table_exists(table) for table in TABLES_REQUERIDAS)


def update_dashboard_key(llave, cantidad):
    """Actualiza la métrica persistida identificada por ``llave``."""

    return Dashboard.objects.update_or_create(
        llave=llave,
        defaults={"cantidad": cantidad},
    )


def update_dashboard_comedores():
    """Refresca el agregado de Comedores y Relevamientos."""

    if not _tablas_requeridas_existen():
        return

    cache.delete_many(DASHBOARD_CACHE_KEYS)
    update_dashboard_key("cantidad_comedores_activos", contar_comedores_activos())
    update_dashboard_key(
        "cantidad_relevamientos_activos", contar_relevamientos_activos()
    )
    update_dashboard_key("presupuesto_desayuno", calcular_presupuesto_desayuno())
    update_dashboard_key("presupuesto_merienda", calcular_presupuesto_merienda())
    update_dashboard_key("presupuesto_comida", calcular_presupuesto_comida())


def register_signals():
    """Registra observers sin consultar la base durante el arranque de Django."""

    observar_comedores(update_dashboard_comedores)
    observar_relevamientos(update_dashboard_comedores)
