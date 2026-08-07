from core.soft_delete import registry


def test_backfill_handlers_usa_orden_estable_por_nombre(monkeypatch):
    monkeypatch.setattr(registry, "_BACKFILL_SIDE_EFFECT_HANDLERS", {})
    zeta = lambda **kwargs: None
    alfa = lambda **kwargs: None
    registry.registrar_backfill_side_effect_handler("zeta", zeta)
    registry.registrar_backfill_side_effect_handler("alfa", alfa)

    assert registry.obtener_backfill_side_effect_handlers() == (alfa, zeta)
