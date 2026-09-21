"""Tests del dato de ejemplar del DNI que RENAPER informa en el payload crudo.

`_extraer_datos_ejemplar_dni` es una función pura sobre el dict de respuesta, así
que se ejercita sin DB ni red: lo que importa es qué hace con un payload
incompleto, con placeholders y con formatos de fecha inesperados.
"""

import pytest

from celiaquia.views.validacion_renaper import _extraer_datos_ejemplar_dni


def _resultado(**datos_api):
    return {"success": True, "data": {}, "datos_api": datos_api}


def test_extrae_emision_vencimiento_y_ejemplar():
    """Formato real del servicio, medido en producción: fechas en dd/mm/aaaa y
    ejemplar como letra. Se muestran tal cual llegan."""
    resultado = _resultado(
        emision="31/05/2019",
        vencimiento="16/05/2027",
        ejemplar="b",
        nombres="Ana",
    )

    assert _extraer_datos_ejemplar_dni(resultado) == {
        "emision": "31/05/2019",
        "vencimiento": "16/05/2027",
        "ejemplar": "B",
    }


def test_fecha_iso_se_convierte_a_formato_local():
    """RENAPER hoy manda dd/mm/aaaa, pero el conversor ISO se conserva por si el
    servicio cambia: una fecha ISO no debe llegar cruda a la pantalla."""
    resultado = _resultado(emision="2019-04-15", ejemplar="A")

    assert _extraer_datos_ejemplar_dni(resultado)["emision"] == "15/04/2019"


def test_sin_datos_de_ejemplar_devuelve_none():
    """El bloque es informativo: si RENAPER no informa nada, no ocupa lugar."""
    assert _extraer_datos_ejemplar_dni(_resultado(nombres="Ana")) is None


@pytest.mark.parametrize("placeholder", ["", "  ", "0", "-", "N/A", "null"])
def test_placeholders_se_tratan_como_ausencia(placeholder):
    resultado = _resultado(
        emision=placeholder, vencimiento=placeholder, ejemplar=placeholder
    )

    assert _extraer_datos_ejemplar_dni(resultado) is None


def test_payload_parcial_conserva_lo_que_vino():
    resultado = _resultado(emision="2019-04-15", vencimiento="0", ejemplar=None)

    assert _extraer_datos_ejemplar_dni(resultado) == {
        "emision": "15/04/2019",
        "vencimiento": None,
        "ejemplar": None,
    }


def test_fecha_en_formato_inesperado_se_muestra_tal_cual():
    """Ante un formato que no se reconoce se prefiere mostrar el valor crudo
    antes que ocultarlo."""
    resultado = _extraer_datos_ejemplar_dni(_resultado(emision="ABR-2019"))

    assert resultado["emision"] == "ABR-2019"


@pytest.mark.parametrize("datos_api", [None, "texto", [], 42])
def test_payload_crudo_ausente_o_invalido_no_rompe(datos_api):
    assert (
        _extraer_datos_ejemplar_dni({"success": True, "datos_api": datos_api}) is None
    )
    assert _extraer_datos_ejemplar_dni({"success": True}) is None
