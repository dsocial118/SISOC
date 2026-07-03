"""Tests for test cruce service."""

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from celiaquia.models import ExpedienteCiudadano
from celiaquia.services.cruce_service import CruceService
from celiaquia.services import cruce_service


# pylint: disable=protected-access
@pytest.mark.parametrize(
    "rol,es_responsable_puro",
    [
        (ExpedienteCiudadano.ROLE_RESPONSABLE, True),
        (ExpedienteCiudadano.ROLE_BENEFICIARIO, False),
        (ExpedienteCiudadano.ROLE_BENEFICIARIO_Y_RESPONSABLE, False),
        ("RESPONSABLE", True),
        ("  responsable  ", True),
        ("", False),
        (None, False),
    ],
)
def test_es_responsable_puro_regla_de_cupo(rol, es_responsable_puro):
    """Solo el responsable puro no ocupa cupo; beneficiario y doble rol sí.

    Garantiza que en el cruce un doble rol (celíaco que además cuida a otro
    celíaco) NO se saltee: se valida como beneficiario y ocupa su propio cupo.
    """
    assert CruceService._es_responsable_puro(rol) is es_responsable_puro


def test_read_file_bytes_disallows_paths():
    with pytest.raises(ValidationError):
        CruceService._read_file_bytes("/etc/passwd")


def test_read_file_bytes_accepts_uploaded_file():
    contenido = b"col1,col2\n1,2"
    archivo = SimpleUploadedFile("test.csv", contenido)
    resultado = CruceService._read_file_bytes(archivo)
    assert resultado == contenido


def test_generar_prd_pdf_html_error_sin_weasy(monkeypatch):
    monkeypatch.setattr(cruce_service, "_WEASY_OK", False)
    with pytest.raises(RuntimeError):
        CruceService._generar_prd_pdf_html(None, {})
