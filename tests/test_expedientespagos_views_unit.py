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
        admision=SimpleNamespace(id=11, num_expediente="EX-CONV-1"),
        total=Decimal("110000000.75"),
        fecha_creacion=date(2026, 7, 13),
    )

    item = _build_expediente_pago_list_item(expediente)

    assert item["pk"] == 3058
    assert item["cells"][4]["content"] == "EX-CONV-1"
    assert item["cells"][5]["content"] == "$110.000.001"
    assert item["cells"][6]["content"] == "13/07/2026"


def test_build_expediente_pago_list_item_escapa_campos_de_texto():
    expediente = SimpleNamespace(
        pk=1,
        mes_pago="<script>alert(1)</script>",
        ano="2026",
        expediente_pago="EX&1",
        expediente_convenio='"><img src=x onerror=alert(1)>',
        admision=None,
        total=Decimal("100.00"),
        fecha_creacion=date(2026, 7, 13),
    )

    item = _build_expediente_pago_list_item(expediente)

    assert "<script>" not in item["cells"][0]["content"]
    assert item["cells"][0]["content"] == "&lt;script&gt;alert(1)&lt;/script&gt;"
    assert item["cells"][2]["content"] == "EX&amp;1"
    assert "<img" not in item["cells"][3]["content"]


def test_build_expediente_pago_list_item_alerta_cuando_no_hay_admision():
    expediente = SimpleNamespace(
        pk=2,
        mes_pago="Abril",
        ano="2026",
        expediente_pago="EX-2",
        expediente_convenio="CONV-2",
        admision=None,
        total=Decimal("100.00"),
        fecha_creacion=date(2026, 7, 13),
    )

    item = _build_expediente_pago_list_item(expediente)

    assert "Sin admisión" in item["cells"][4]["content"]


def test_build_expediente_pago_list_item_escapa_el_expediente_de_la_admision():
    expediente = SimpleNamespace(
        pk=3,
        mes_pago="Mayo",
        ano="2026",
        expediente_pago="EX-3",
        expediente_convenio="CONV-3",
        admision=SimpleNamespace(id=12, num_expediente='"><img src=x>'),
        total=Decimal("100.00"),
        fecha_creacion=date(2026, 7, 13),
    )

    item = _build_expediente_pago_list_item(expediente)

    assert "<img" not in item["cells"][4]["content"]
