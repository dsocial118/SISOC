from importlib import import_module

import pytest


migration_0042 = import_module(
    "centrodeinfancia.migrations.0042_alter_nominacentroinfancia_talla"
)


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        ("95", "95.0"),
        (" 95,5 ", "95.5"),
        ("95.50", "95.5"),
        ("", None),
    ],
)
def test_normaliza_talla_legacy_convertible_sin_perder_precision(valor, esperado):
    assert migration_0042.normalizar_talla_legacy(valor) == esperado


@pytest.mark.parametrize("valor", ["alto", "95.55", "10000", "NaN"])
def test_rechaza_talla_legacy_ambigua_o_fuera_de_capacidad(valor):
    with pytest.raises(ValueError):
        migration_0042.normalizar_talla_legacy(valor)
