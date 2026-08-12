"""Actualización de métricas del dashboard mediante contratos de dominio."""

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


def update_dashboard_key(llave, cantidad):
    """Actualiza la métrica persistida identificada por ``llave``."""

    return Dashboard.objects.update_or_create(
        llave=llave,
        defaults={"cantidad": cantidad},
    )


def update_dashboard_comedores():
    """Refresca el agregado de Comedores y Relevamientos."""

    update_dashboard_key("cantidad_comedores_activos", contar_comedores_activos())
    update_dashboard_key(
        "cantidad_relevamientos_activos", contar_relevamientos_activos()
    )
    update_dashboard_key("presupuesto_desayuno", calcular_presupuesto_desayuno())
    update_dashboard_key("presupuesto_merienda", calcular_presupuesto_merienda())
    update_dashboard_key("presupuesto_comida", calcular_presupuesto_comida())


def register_signals():
    """Registra los observers cuando las tablas requeridas ya existen."""

    if not all(
        table_exists(table)
        for table in (
            "comedores_comedor",
            "relevamientos_relevamiento",
            "relevamientos_prestacion",
            "comedores_valorcomida",
        )
    ):
        return

    observar_comedores(update_dashboard_comedores)
    observar_relevamientos(update_dashboard_comedores)
