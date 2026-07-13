from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from expedientespagos.views import _build_expediente_pago_list_item


def test_build_expediente_pago_list_item_formatea_total_sin_decimales():
    expediente = SimpleNamespace(
        pk=3058,
        mes_pago="Marzo",
        ano=2026,
        expediente_pago="EX-1",
        expediente_convenio="CONV-1",
        total=Decimal("110000000.75"),
        fecha_creacion=date(2026, 7, 13),
    )

    item = _build_expediente_pago_list_item(expediente)

    assert item["pk"] == 3058
    assert item["cells"][4]["content"] == "$110.000.001"
    assert item["cells"][5]["content"] == "13/07/2026"
