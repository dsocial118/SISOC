from decimal import Decimal

import pytest

from core.templatetags.custom_filters import monto_sin_decimales


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (Decimal("110000000.00"), "110.000.000"),
        (Decimal("1234.56"), "1.235"),
        ("9876543.21", "9.876.543"),
        (None, "-"),
        ("", "-"),
        ("no-es-monto", "-"),
    ],
)
def test_monto_sin_decimales_formatea_pesos_sin_centavos(value, expected):
    assert monto_sin_decimales(value) == expected
