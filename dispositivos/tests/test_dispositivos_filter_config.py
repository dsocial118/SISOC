from dispositivos.dispositivos_filter_config import get_filters_ui_config


def _field(config, name):
    return next(field for field in config["fields"] if field["name"] == name)


def test_filtros_choice_exponen_opciones_para_advanced_filters():
    config = get_filters_ui_config()

    tipo_dispositivo = _field(config, "tipo_dispositivo")
    modalidad = _field(config, "modalidad_funcionamiento")
    capacidad = _field(config, "capacidad_total_plazas")

    assert {"value": "refugio", "label": "Refugio"} in tipo_dispositivo["choices"]
    assert {"value": "permanente", "label": "Permanente (todo el año)"} in modalidad[
        "choices"
    ]
    assert {"value": "16_30", "label": "16 a 30 plazas"} in capacidad["choices"]
