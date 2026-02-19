"""Tests for test cruce service."""

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from celiaquia.services.cruce_service import CruceService
from celiaquia.services import cruce_service


# pylint: disable=protected-access
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
