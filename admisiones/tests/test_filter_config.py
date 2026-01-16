"""Tests for filter configuration order and structure."""

import pytest
from admisiones.services.admisiones_filter_config import (
    FILTER_FIELDS as ADMISIONES_FILTER_FIELDS,
    get_filters_ui_config as get_admisiones_filters_ui_config,
)
from admisiones.services.legales_filter_config import (
    FILTER_FIELDS as LEGALES_FILTER_FIELDS,
    get_filters_ui_config as get_legales_filters_ui_config,
)


# Common required fields for both configurations
REQUIRED_FILTER_FIELDS = [
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


class TestAdmisionesFilterConfig:
    """Test filter configuration for admisiones tecnicos."""

    def test_comedor_nombre_is_first_field(self):
        """Verify that 'Nombre del comedor' is the first filter field."""
        assert len(ADMISIONES_FILTER_FIELDS) > 0
        first_field = ADMISIONES_FILTER_FIELDS[0]
        assert first_field["name"] == "comedor_nombre"
        assert first_field["label"] == "Nombre del comedor"
        assert first_field["type"] == "text"

    def test_all_required_fields_present(self):
        """Verify all required fields are present in the filter config."""
        field_names = [field["name"] for field in ADMISIONES_FILTER_FIELDS]

        for required_field in REQUIRED_FILTER_FIELDS:
            assert required_field in field_names, f"Field {required_field} not found"

    def test_filters_ui_config_structure(self):
        """Verify the UI config returns proper structure."""
        config = get_admisiones_filters_ui_config()

        assert "fields" in config
        assert "operators" in config
        assert isinstance(config["fields"], list)
        assert len(config["fields"]) > 0

        # First field should be comedor_nombre
        assert config["fields"][0]["name"] == "comedor_nombre"


class TestLegalesFilterConfig:
    """Test filter configuration for admisiones legales."""

    def test_comedor_nombre_is_first_field(self):
        """Verify that 'Nombre del comedor' is the first filter field."""
        assert len(LEGALES_FILTER_FIELDS) > 0
        first_field = LEGALES_FILTER_FIELDS[0]
        assert first_field["name"] == "comedor_nombre"
        assert first_field["label"] == "Nombre del comedor"
        assert first_field["type"] == "text"

    def test_all_required_fields_present(self):
        """Verify all required fields are present in the filter config."""
        field_names = [field["name"] for field in LEGALES_FILTER_FIELDS]

        for required_field in REQUIRED_FILTER_FIELDS:
            assert required_field in field_names, f"Field {required_field} not found"

    def test_filters_ui_config_structure(self):
        """Verify the UI config returns proper structure."""
        config = get_legales_filters_ui_config()

        assert "fields" in config
        assert "operators" in config
        assert isinstance(config["fields"], list)
        assert len(config["fields"]) > 0

        # First field should be comedor_nombre
        assert config["fields"][0]["name"] == "comedor_nombre"
