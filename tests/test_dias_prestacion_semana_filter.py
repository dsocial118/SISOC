"""Tests for test dias prestacion semana filter."""

from types import SimpleNamespace

from core.templatetags.custom_filters import dias_prestacion_semana


def test_dias_prestacion_semana_devuelve_guion_si_no_hay_prestacion():
    assert dias_prestacion_semana(None) == "-"


def test_dias_prestacion_semana_cuenta_dias_con_al_menos_una_comida():
    prestacion = SimpleNamespace(
        lunes_desayuno_actual=10,
        martes_almuerzo_actual="0",
        miercoles_merienda_actual="2",
        jueves_cena_actual="-",
    )

    assert dias_prestacion_semana(prestacion) == 2


def test_dias_prestacion_semana_devuelve_guion_si_todos_son_cero_o_vacios():
    prestacion = SimpleNamespace(
        lunes_desayuno_actual=0,
        martes_almuerzo_actual="0",
        miercoles_merienda_actual=None,
        jueves_cena_actual="",
        viernes_desayuno_actual="-",
    )

    assert dias_prestacion_semana(prestacion) == "-"


def test_dias_prestacion_semana_incluye_merienda_reforzada():
    prestacion = SimpleNamespace(
        lunes_merienda_reforzada_actual=3,
        martes_merienda_reforzada_actual=0,
    )

    assert dias_prestacion_semana(prestacion) == 1


def test_dias_prestacion_semana_usa_aprobadas_informe_tecnico():
    informe = SimpleNamespace(
        aprobadas_desayuno_lunes=0,
        aprobadas_almuerzo_lunes=None,
        aprobadas_merienda_lunes="0",
        aprobadas_cena_lunes="-",
        aprobadas_desayuno_martes=5,
        aprobadas_almuerzo_miercoles="2",
    )

    assert dias_prestacion_semana(informe) == 2
