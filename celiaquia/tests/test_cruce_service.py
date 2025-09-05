import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from celiaquia.services.cruce_service import CruceService


def test_read_file_bytes_disallows_paths():
    with pytest.raises(ValidationError):
        CruceService._read_file_bytes("/etc/passwd")


def test_read_file_bytes_accepts_uploaded_file():
    contenido = b"col1,col2\n1,2"
    archivo = SimpleUploadedFile("test.csv", contenido)
    resultado = CruceService._read_file_bytes(archivo)
    assert resultado == contenido
