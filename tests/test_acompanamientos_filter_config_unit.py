"""Tests de la configuracion de filtros del listado de acompanamientos."""

import logging

from acompanamientos.services.filter_config import (
    FIELD_MAP,
    FILTER_FIELDS,
    get_filters_ui_config,
)
from duplas.models import Dupla


def test_filtros_acompanamiento_replican_campos_clave_de_admisiones():
    assert [field["name"] for field in FILTER_FIELDS] == [
        "comedor_nombre",
        "comedor_id",
        "tipo_admision",
        "organizacion",
        "num_expediente",
        "provincia",
        "equipo_tecnico",
        "estado",
        "fecha_modificado",
    ]
    assert FIELD_MAP["comedor_nombre"] == "nombre"
    assert FIELD_MAP["estado"] == "acompanamiento_estado_admision"


def test_config_ui_acompanamiento_incluye_operadores_y_choices():
    config = get_filters_ui_config()
    fields = {field["name"]: field for field in config["fields"]}

    assert set(config["operators"]) == {"text", "number", "date", "choice"}
    assert fields["tipo_admision"]["type"] == "choice"
    assert fields["estado"]["type"] == "choice"


def test_config_ui_registra_falla_al_cargar_choices(mocker, caplog):
    mocker.patch.object(Dupla.objects, "activas", side_effect=RuntimeError("db"))

    with caplog.at_level(logging.ERROR):
        get_filters_ui_config()

    assert "No se pudieron cargar las opciones de filtros de acompanamientos" in caplog.text
