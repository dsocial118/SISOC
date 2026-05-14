"""
Tests de validación condicional de CiudadanoForm según tipo_registro_identidad.
Fase 4 — identidad ciudadano.

No requieren DB: los ModelChoiceField (provincia/municipio/localidad) no se someten
porque son opcionales y los querysets son lazy.
"""

import pytest

from ciudadanos.forms import CiudadanoForm
from ciudadanos.models import Ciudadano


def _data(**kwargs):
    """Datos base válidos para ESTANDAR; el caller pisa lo que necesite."""
    defaults = {
        "tipo_registro_identidad": Ciudadano.TIPO_REGISTRO_ESTANDAR,
        "apellido": "Perez",
        "nombre": "Juan",
        "fecha_nacimiento": "1990-01-01",
        "tipo_documento": Ciudadano.DOCUMENTO_DNI,
        "documento": "12345678",
        # ModelChoiceFields opcionales — no se someten
    }
    defaults.update(kwargs)
    return defaults


# --- ESTANDAR ---


def test_estandar_completo_es_valido():
    assert CiudadanoForm(data=_data()).is_valid()


@pytest.mark.parametrize(
    "campo", ["apellido", "nombre", "fecha_nacimiento", "documento"]
)
def test_estandar_falta_campo_requerido(campo):
    form = CiudadanoForm(data=_data(**{campo: ""}))
    assert not form.is_valid()
    assert campo in form.errors


# --- SIN_DNI ---


def test_sin_dni_sin_motivo_falla():
    form = CiudadanoForm(
        data=_data(
            tipo_registro_identidad=Ciudadano.TIPO_REGISTRO_SIN_DNI,
            documento="",
            motivo_sin_dni="",
        )
    )
    assert not form.is_valid()
    assert "motivo_sin_dni" in form.errors


def test_sin_dni_con_motivo_es_valido():
    form = CiudadanoForm(
        data=_data(
            tipo_registro_identidad=Ciudadano.TIPO_REGISTRO_SIN_DNI,
            documento="",
            motivo_sin_dni=Ciudadano.MOTIVO_SIN_DNI_OTRO,
        )
    )
    assert form.is_valid(), form.errors


def test_sin_dni_con_documento_lo_limpia():
    form = CiudadanoForm(
        data=_data(
            tipo_registro_identidad=Ciudadano.TIPO_REGISTRO_SIN_DNI,
            documento="12345678",
            motivo_sin_dni=Ciudadano.MOTIVO_SIN_DNI_OTRO,
        )
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["documento"] is None


def test_sin_dni_con_motivo_admite_fecha_vacia():
    form = CiudadanoForm(
        data=_data(
            tipo_registro_identidad=Ciudadano.TIPO_REGISTRO_SIN_DNI,
            documento="",
            fecha_nacimiento="",
            motivo_sin_dni=Ciudadano.MOTIVO_SIN_DNI_OTRO,
        )
    )
    assert form.is_valid(), form.errors


# --- DNI_NO_VALIDADO_RENAPER ---


def test_no_validado_sin_documento_falla():
    form = CiudadanoForm(
        data=_data(
            tipo_registro_identidad=Ciudadano.TIPO_REGISTRO_DNI_NO_VALIDADO,
            documento="",
            motivo_no_validacion_renaper=Ciudadano.MOTIVO_NO_VALIDADO_OTRO,
        )
    )
    assert not form.is_valid()
    assert "documento" in form.errors


def test_no_validado_sin_motivo_renaper_falla():
    form = CiudadanoForm(
        data=_data(
            tipo_registro_identidad=Ciudadano.TIPO_REGISTRO_DNI_NO_VALIDADO,
            documento="12345678",
            motivo_no_validacion_renaper="",
        )
    )
    assert not form.is_valid()
    assert "motivo_no_validacion_renaper" in form.errors


def test_no_validado_completo_es_valido():
    form = CiudadanoForm(
        data=_data(
            tipo_registro_identidad=Ciudadano.TIPO_REGISTRO_DNI_NO_VALIDADO,
            documento="12345678",
            motivo_no_validacion_renaper=Ciudadano.MOTIVO_NO_VALIDADO_OTRO,
        )
    )
    assert form.is_valid(), form.errors
