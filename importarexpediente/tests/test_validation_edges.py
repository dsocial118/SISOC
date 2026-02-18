"""Tests for test validation edges."""

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from comedores.models import Comedor
from importarexpediente.models import (
    ArchivosImportados,
    ErroresImportacion,
    ExitoImportacion,
)

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def user(db):
    return User.objects.create_user(username="tester", password="pass1234")


@pytest.fixture
def client_logged(client, user):
    client.login(username="tester", password="pass1234")
    return client


@pytest.fixture
def tmp_media(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
    return settings.MEDIA_ROOT


def test_upload_without_header_is_rejected(client_logged, tmp_media):
    comedor = Comedor.objects.create(nombre="C")
    content = "ID;COMEDOR;Expediente de Pago\n{};Anexo;EX-2025-ERR\n".format(comedor.pk)
    uploaded = SimpleUploadedFile(
        "x.csv", content.encode("utf-8"), content_type="text/csv"
    )

    resp = client_logged.post(
        reverse("upload"),
        {"file": uploaded, "delimiter": ";", "has_header": False},
    )
    assert resp.status_code in (302, 200)
    batch = ArchivosImportados.objects.latest("id")
    assert batch.count_errores == 1
    assert ErroresImportacion.objects.filter(archivo_importado=batch, fila=0).exists()
    assert ExitoImportacion.objects.filter(archivo_importado=batch).count() == 0


def test_upload_with_invalid_numbers_creates_error(client_logged, tmp_media):
    Comedor.objects.create(nombre="Comedor X")
    # Invalid numeric in 'Monto Mensuales Desayuno' and invalid year
    content = (
        "ID;COMEDOR;EXPEDIENTE del CONVENIO;Expediente de Pago;Monto Mensuales Desayuno;TOTAL;Mes de Pago;Año\n"
        "9999;Anexo Norte;EX-2024-ERR;EX-2025-ERR;ABC;$ 100,00;enero;XX\n"
    )
    uploaded = SimpleUploadedFile(
        "bad.csv", content.encode("utf-8"), content_type="text/csv"
    )

    resp = client_logged.post(
        reverse("upload"),
        {"file": uploaded, "delimiter": ";", "has_header": True},
    )
    assert resp.status_code in (302, 200)

    batch = ArchivosImportados.objects.latest("id")
    # Should register an error for the invalid row
    assert ErroresImportacion.objects.filter(archivo_importado=batch).count() >= 1
    # And no success
    assert ExitoImportacion.objects.filter(archivo_importado=batch).count() == 0
