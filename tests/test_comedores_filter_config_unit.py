"""Tests unitarios para la configuración de filtros de comedores."""

from comedores.services.filter_config import (
    BOOL_OPS,
    FIELD_MAP,
    FIELD_TYPES,
    get_filters_ui_config,
)


def test_get_filters_ui_config_incluye_operadores_booleanos():
    config = get_filters_ui_config()

    assert config["operators"]["boolean"] == list(BOOL_OPS)
    assert any(
        field["name"] == "es_judicializado" and field["type"] == "boolean"
        for field in config["fields"]
    )


def test_config_estados_no_expone_actividad_y_ofrece_choices_legibles():
    config = get_filters_ui_config()
    fields = {field["name"]: field for field in config["fields"]}

    assert "estado_actividad" not in fields
    assert "estado_actividad" not in FIELD_MAP
    assert "estado_actividad" not in FIELD_TYPES
    assert fields["estado_general"]["type"] == "choice"
    assert fields["estado_general"]["choices"] == [
        {"value": "Activo", "label": "Activo"},
        {"value": "Inactivo", "label": "Inactivo"},
    ]
    assert all(
        choice["value"] == choice["label"]
        for name in ("estado_proceso", "estado_detalle")
        for choice in fields[name].get("choices", [])
    )
