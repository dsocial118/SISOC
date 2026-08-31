from datetime import date
from decimal import Decimal

from django.core.cache import cache

from comedores.models import Comedor, ValorComida
from dashboard import signals
from dashboard.models import Dashboard
from dashboard.utils import (
    calcular_presupuesto_comida,
    calcular_presupuesto_desayuno,
    calcular_presupuesto_merienda,
    contar_comedores_activos,
)
from relevamientos.api import contar_relevamientos


def test_dashboard_uses_public_comedores_projection(db):
    cache.clear()
    Comedor.objects.create(nombre="Espacio de prueba")
    ValorComida.objects.create(
        tipo="desayuno", valor=Decimal("12.50"), fecha=date.today()
    )
    ValorComida.objects.create(
        tipo="merienda", valor=Decimal("7.50"), fecha=date.today()
    )
    ValorComida.objects.create(
        tipo="comida", valor=Decimal("20.00"), fecha=date.today()
    )

    assert contar_comedores_activos() == 1
    assert calcular_presupuesto_desayuno() == Decimal("12.50")
    assert calcular_presupuesto_merienda() == Decimal("7.50")
    assert calcular_presupuesto_comida() == Decimal("20.00")


def test_relevamientos_public_count_starts_empty(db):
    assert contar_relevamientos() == 0


def test_dashboard_refresh_invalidates_cached_metrics_before_persisting(db, mocker):
    cache.clear()
    metrics = (
        ("contar_comedores_activos", "cantidad_comedores_activos", 3),
        ("contar_relevamientos_activos", "cantidad_relevamientos_activos", 4),
        ("calcular_presupuesto_desayuno", "presupuesto_desayuno", 5),
        ("calcular_presupuesto_merienda", "presupuesto_merienda", 6),
        ("calcular_presupuesto_comida", "presupuesto_comida", 7),
    )
    for cache_key, _dashboard_key, _value in metrics:
        cache.set(cache_key, 0)

    mocker.patch.object(signals, "_tablas_requeridas_existen", return_value=True)

    for function_name, cache_key, value in metrics:

        def calculate(key=cache_key, result=value):
            assert cache.get(key) is None
            return result

        mocker.patch.object(signals, function_name, side_effect=calculate)

    signals.update_dashboard_comedores()

    assert dict(Dashboard.objects.values_list("llave", "cantidad")) == {
        dashboard_key: value for _cache_key, dashboard_key, value in metrics
    }
