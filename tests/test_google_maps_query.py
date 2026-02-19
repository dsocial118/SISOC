"""Tests for test google maps query."""

import pytest

from core.templatetags.custom_filters import google_maps_query


def test_google_maps_query_normalizes_comma_decimal():
    result = google_maps_query("-34,671619", "-58,41097")
    assert result == "-34.671619,-58.41097"
    assert result.count(",") == 1


@pytest.mark.parametrize(
    "latitud,longitud",
    [
        (91, 0),
        (-91, 0),
        (0, 181),
        (0, -181),
    ],
)
def test_google_maps_query_rejects_out_of_range(latitud, longitud):
    assert google_maps_query(latitud, longitud) == ""


@pytest.mark.parametrize(
    "latitud,longitud",
    [
        ("34,67,1", "58,4"),
        ("foo", "58.4"),
        ("-34.0", "bar"),
    ],
)
def test_google_maps_query_rejects_invalid_format(latitud, longitud):
    assert google_maps_query(latitud, longitud) == ""


def test_google_maps_query_accepts_numeric_values():
    assert google_maps_query(-34, -58) == "-34,-58"
