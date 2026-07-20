"""Tests unitarios para comedores.utils — funciones de conformidad y detección de programa."""

from datetime import date
from types import SimpleNamespace

import pytest

import comedores.utils as module


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _comedor(nombre):
    return SimpleNamespace(
        programa_id=99,
        programa=SimpleNamespace(nombre=nombre),
    )


def _comedor_sin_programa():
    return SimpleNamespace(programa_id=None, programa=None)


# ---------------------------------------------------------------------------
# _normalize_programa
# ---------------------------------------------------------------------------


def test_normalize_programa_remueve_acentos():
    assert module._normalize_programa("Abordaje Comunitário") == "abordaje comunitario"
    assert module._normalize_programa("Alimentar Comunidad") == "alimentar comunidad"
    assert module._normalize_programa("  Línea  Secos  ") == "linea secos"


# ---------------------------------------------------------------------------
# is_prestacion_alimentaria_conformidad_program
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "nombre,expected",
    [
        ("Alimentar Comunidad", True),
        ("alimentar comunidad", True),
        ("ALIMENTAR COMUNIDAD", True),
        # Con tilde en caso de variante tipográfica
        ("Álimentar Comunidad", True),
        ("Abordaje Comunitario", True),
        ("Abordaje Comunitario - Linea Secos", True),
        # Con acentos en "Comunitário"
        ("Abordaje Comunitário", True),
        ("PNUD Programa 1", False),
        ("Otro Programa", False),
        ("", False),
    ],
)
def test_is_prestacion_alimentaria_conformidad_program(nombre, expected):
    assert (
        module.is_prestacion_alimentaria_conformidad_program(_comedor(nombre))
        is expected
    )


def test_is_prestacion_alimentaria_conformidad_program_sin_programa():
    assert (
        module.is_prestacion_alimentaria_conformidad_program(_comedor_sin_programa())
        is False
    )


# ---------------------------------------------------------------------------
# is_abordaje_comunitario_linea_secos_program
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "nombre,expected",
    [
        ("Abordaje Comunitario - Linea Secos", True),
        ("abordaje comunitario linea secos", True),
        # Sin "linea secos"
        ("Abordaje Comunitario", False),
        # Sin "abordaje comunitario"
        ("Linea Secos", False),
        ("Alimentar Comunidad", False),
        ("", False),
    ],
)
def test_is_abordaje_comunitario_linea_secos_program(nombre, expected):
    assert (
        module.is_abordaje_comunitario_linea_secos_program(_comedor(nombre)) is expected
    )


# ---------------------------------------------------------------------------
# is_abordaje_comunitario_relevamientos_header_program
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "nombre,expected",
    [
        ("Abordaje Comunitario - Linea Secos", True),
        ("Abordaje Comunitario - Línea Secos", True),
        ("Abordaje Comunitario - Linea Tradicional", True),
        ("Abordaje Comunitario - Línea Tradicional", True),
        ("Abordaje Comunitario", False),
        ("Linea Secos", False),
        ("Linea Tradicional", False),
        ("PNUD Prog Especial", False),
        ("Alimentar Comunidad", False),
        ("", False),
    ],
)
def test_is_abordaje_comunitario_relevamientos_header_program(nombre, expected):
    assert (
        module.is_abordaje_comunitario_relevamientos_header_program(_comedor(nombre))
        is expected
    )


# ---------------------------------------------------------------------------
# add_months_period
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "start,months,expected",
    [
        (date(2026, 1, 1), -1, date(2025, 12, 1)),  # enero → diciembre anterior
        (date(2026, 1, 1), 1, date(2026, 2, 1)),
        (date(2026, 12, 1), 1, date(2027, 1, 1)),
        (date(2026, 6, 1), -6, date(2025, 12, 1)),
    ],
)
def test_add_months_period(start, months, expected):
    assert module.add_months_period(start, months) == expected


# ---------------------------------------------------------------------------
# get_prestacion_conformidad_periods
# ---------------------------------------------------------------------------


def _mock_sin_rendicion(mocker):
    mocker.patch.object(
        module,
        "get_prestacion_conformidad_convenio_bounds",
        return_value=None,
    )


def _mock_con_bounds(mocker, start, end):
    mocker.patch.object(
        module,
        "get_prestacion_conformidad_convenio_bounds",
        return_value=(start, end),
    )


def _mock_today(mocker, today):
    mocker.patch("comedores.utils.timezone.localdate", return_value=today)


def test_get_prestacion_conformidad_periods_sin_rendicion(mocker):
    _mock_sin_rendicion(mocker)
    _mock_today(mocker, date(2026, 6, 17))

    comedor = _comedor("Alimentar Comunidad")
    periods = module.get_prestacion_conformidad_periods(comedor)

    assert len(periods) == 6
    assert periods[0] == date(2026, 5, 1)
    assert periods[1] == date(2026, 4, 1)
    assert periods[-1] == date(2025, 12, 1)


def test_get_prestacion_conformidad_periods_enero_rollover(mocker):
    _mock_sin_rendicion(mocker)
    _mock_today(mocker, date(2026, 1, 15))

    comedor = _comedor("Alimentar Comunidad")
    periods = module.get_prestacion_conformidad_periods(comedor)

    assert periods[0] == date(2025, 12, 1)
    assert len(periods) == 6


def test_get_prestacion_conformidad_periods_con_bounds(mocker):
    _mock_today(mocker, date(2026, 6, 17))
    _mock_con_bounds(mocker, date(2026, 3, 1), date(2026, 8, 1))

    comedor = _comedor("Alimentar Comunidad")
    periods = module.get_prestacion_conformidad_periods(comedor)

    # Solo meses >= 2026-03 y <= 2026-08, hasta el mes anterior al actual
    assert all(date(2026, 3, 1) <= p <= date(2026, 8, 1) for p in periods)
    assert date(2026, 5, 1) in periods


def test_get_prestacion_conformidad_periods_todos_fuera_de_bounds(mocker):
    _mock_today(mocker, date(2026, 6, 17))
    # Bounds en el futuro: no debería devolver ningún período
    _mock_con_bounds(mocker, date(2027, 1, 1), date(2027, 6, 1))

    comedor = _comedor("Alimentar Comunidad")
    periods = module.get_prestacion_conformidad_periods(comedor)

    assert periods == []


def test_get_prestacion_conformidad_periods_limit(mocker):
    _mock_sin_rendicion(mocker)
    _mock_today(mocker, date(2026, 6, 17))

    comedor = _comedor("Alimentar Comunidad")
    assert len(module.get_prestacion_conformidad_periods(comedor, limit=3)) == 3
    assert len(module.get_prestacion_conformidad_periods(comedor, limit=1)) == 1


# ---------------------------------------------------------------------------
# get_prestacion_conformidad_pending_period
# ---------------------------------------------------------------------------


def test_get_prestacion_conformidad_pending_period_devuelve_periodo_anterior(mocker):
    _mock_sin_rendicion(mocker)
    _mock_today(mocker, date(2026, 6, 17))

    comedor = _comedor("Alimentar Comunidad")
    result = module.get_prestacion_conformidad_pending_period(comedor)

    assert result == date(2026, 5, 1)
