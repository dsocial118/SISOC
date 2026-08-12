from datetime import date
from decimal import Decimal

from django.core.cache import cache

from comedores.models import Comedor, ValorComida
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
