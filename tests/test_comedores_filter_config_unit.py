"""Tests unitarios para la configuración de filtros de comedores."""

from comedores.services.filter_config import BOOL_OPS, get_filters_ui_config


def test_get_filters_ui_config_incluye_operadores_booleanos():
    config = get_filters_ui_config()

    assert config["operators"]["boolean"] == list(BOOL_OPS)
    assert any(
        field["name"] == "es_judicializado" and field["type"] == "boolean"
        for field in config["fields"]
    )
