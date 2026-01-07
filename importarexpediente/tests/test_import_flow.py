import io
from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from comedores.models import Comedor
from expedientespagos.models import ExpedientePago
from importarexpediente.models import (
    ArchivosImportados,
    ErroresImportacion,
    ExitoImportacion,
    RegistroImportado,
)


User = get_user_model()

# Enable DB access for all tests in this module
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


def _make_csv(comedor_pk):
    # Headers are case-insensitive and mapped via HEADER_MAP in views
    # Use comma delimiter and quote localized decimal to avoid column split
    content = (
        "Expediente,Comedor,ID,Monto,Fecha pago al banco,Fecha acreditacion,Numero Orden Pago,Observaciones\n"
        f'EXP-001,Anexo Norte,{comedor_pk},"1.234,56",05/01/2024,10/01/2024,OP-9,Observación de prueba\n'
    )
    return content


def test_upload_validation_success_creates_batch_and_logs_success(
    client_logged, tmp_media, db
):
    comedor = Comedor.objects.create(nombre="Comedor Uno")

    csv_bytes = _make_csv(comedor.pk).encode("utf-8")
    uploaded = SimpleUploadedFile("expedientes.csv", csv_bytes, content_type="text/csv")

    url = reverse("upload")
    resp = client_logged.post(
        url,
        {
            "file": uploaded,
            "delimiter": ",",
            "has_header": True,
        },
        follow=True,
    )

    assert resp.status_code in (302, 200)

    # One master record is created
    assert ArchivosImportados.objects.count() == 1
    batch = ArchivosImportados.objects.first()

    # Success logged, no errors
    assert ExitoImportacion.objects.filter(archivo_importado=batch).count() == 1
    assert ErroresImportacion.objects.filter(archivo_importado=batch).count() == 0

    # Counters persisted in master
    batch.refresh_from_db()
    assert batch.count_exitos == 1
    assert batch.count_errores == 0


def test_upload_validation_empty_csv_logs_error_and_counters(
    client_logged, tmp_media, db
):
    uploaded = SimpleUploadedFile("vacio.csv", b"", content_type="text/csv")
    url = reverse("upload")
    resp = client_logged.post(
        url,
        {
            "file": uploaded,
            "delimiter": ",",
            "has_header": True,
        },
    )
    assert resp.status_code in (302, 200)
    # If form was invalid, there will be no batch
    if ArchivosImportados.objects.count() == 0:
        return

    # Otherwise, a batch should exist with one error and zero successes
    batch = ArchivosImportados.objects.order_by("-id").first()
    assert batch is not None
    batch.refresh_from_db()
    assert batch.count_exitos == 0
    assert batch.count_errores == 1
    assert ErroresImportacion.objects.filter(archivo_importado=batch, fila=0).exists()


def test_import_persists_expedientepago_and_marks_completed(
    client_logged, tmp_media, db
):
    comedor = Comedor.objects.create(nombre="Comedor Dos")

    # Step 1: upload to create batch and success log
    csv_bytes = _make_csv(comedor.pk).encode("utf-8")
    uploaded = SimpleUploadedFile("expedientes.csv", csv_bytes, content_type="text/csv")
    upload_url = reverse("upload")
    client_logged.post(
        upload_url,
        {
            "file": uploaded,
            "delimiter": ",",
            "has_header": True,
        },
    )

    batch = ArchivosImportados.objects.latest("id")

    # Step 2: import
    import_url = reverse("importar_datos", kwargs={"id_archivo": batch.id})
    resp = client_logged.get(import_url)
    assert resp.status_code in (302, 200)

    # One ExpedientePago created
    assert ExpedientePago.objects.count() == 1
    exp = ExpedientePago.objects.first()
    assert exp is not None
    # Check key fields parsed
    assert exp.anexo == "Anexo Norte"
    assert exp.comedor == comedor
    assert exp.fecha_pago_al_banco == date(2024, 1, 5)
    assert exp.fecha_acreditacion == date(2024, 1, 10)

    # RegistroImportado linking success entry with expediente
    assert RegistroImportado.objects.count() == 1

    # Batch marked completed
    batch.refresh_from_db()
    assert batch.importacion_completada is True


def test_import_is_idempotent_when_completed(client_logged, tmp_media, db):
    comedor = Comedor.objects.create(nombre="Comedor Tres")

    csv_bytes = _make_csv(comedor.pk).encode("utf-8")
    uploaded = SimpleUploadedFile("expedientes.csv", csv_bytes, content_type="text/csv")
    client_logged.post(
        reverse("upload"),
        {"file": uploaded, "delimiter": ",", "has_header": True},
    )
    batch = ArchivosImportados.objects.latest("id")

    # First import
    client_logged.get(reverse("importar_datos", kwargs={"id_archivo": batch.id}))
    assert ExpedientePago.objects.count() == 1

    # Second import should not create more
    resp = client_logged.get(
        reverse("importar_datos", kwargs={"id_archivo": batch.id}), follow=True
    )
    assert resp.status_code == 200
    assert ExpedientePago.objects.count() == 1


def test_delete_resets_flag_and_removes_records(client_logged, tmp_media, db):
    comedor = Comedor.objects.create(nombre="Comedor Cuatro")

    csv_bytes = _make_csv(comedor.pk).encode("utf-8")
    uploaded = SimpleUploadedFile("expedientes.csv", csv_bytes, content_type="text/csv")
    client_logged.post(
        reverse("upload"),
        {"file": uploaded, "delimiter": ",", "has_header": True},
    )
    batch = ArchivosImportados.objects.latest("id")

    # Import to create records
    client_logged.get(reverse("importar_datos", kwargs={"id_archivo": batch.id}))
    assert ExpedientePago.objects.count() == 1
    batch.refresh_from_db()
    assert batch.importacion_completada is True

    # Delete imported data
    resp = client_logged.get(
        reverse("borrar_datos_importados", kwargs={"id_archivo": batch.id})
    )
    assert resp.status_code in (302, 200)

    # All imported records removed and flag reset
    assert ExpedientePago.objects.count() == 0
    assert RegistroImportado.objects.count() == 0
    batch.refresh_from_db()
    assert batch.importacion_completada is False
