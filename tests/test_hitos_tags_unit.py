from types import SimpleNamespace

from acompanamientos.templatetags.hitos_tags import render_hito


def test_render_hito_with_completed_value_and_date():
    hitos = SimpleNamespace(retiro_tarjeta=True)
    fechas_hitos = {"retiro_tarjeta": "2025-01-15"}

    context = render_hito(
        hitos=hitos,
        fechas_hitos=fechas_hitos,
        campo="retiro_tarjeta",
        descripcion="Retiro de Tarjeta",
        comedor=123,
        es_tecnico_comedor=True,
    )

    assert context == {
        "campo": "retiro_tarjeta",
        "descripcion": "Retiro de Tarjeta",
        "hito_completado": True,
        "fecha_hito": "2025-01-15",
        "comedor": 123,
        "es_tecnico_comedor": True,
    }


def test_render_hito_defaults_when_hitos_and_dates_are_missing():
    context = render_hito(
        hitos=None,
        fechas_hitos=None,
        campo="retiro_tarjeta",
        descripcion="Retiro de Tarjeta",
        comedor=None,
        es_tecnico_comedor=False,
    )

    assert context["hito_completado"] is False
    assert context["fecha_hito"] is None
    assert context["es_tecnico_comedor"] is False
