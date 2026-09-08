from core.services import fixture_post_load


def test_ejecutar_handlers_usa_orden_estable_por_nombre(monkeypatch):
    monkeypatch.setattr(fixture_post_load, "_HANDLERS", {})
    fixture_post_load.registrar_fixture_post_load_handler("zeta", lambda: "zeta")
    fixture_post_load.registrar_fixture_post_load_handler("alfa", lambda: "alfa")

    assert fixture_post_load.ejecutar_fixture_post_load_handlers() == ("alfa", "zeta")
