import io
from datetime import date
from decimal import Decimal

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
    # Sample aligned to new HEADER_MAP (semicolon-delimited)
    headers = (
        "ID;COMEDOR;ORGANIZACIÓN;EXPEDIENTE del CONVENIO;Expediente de Pago;"
        "Prestaciones Mensuales Desayuno;Prestaciones Mensuales Almuerzo;"
        "Prestaciones Mensuales Merienda;Prestaciones Mensuales Cena;"
        "Monto Mensuales Desayuno;Monto Mensuales Almuerzo;"
        "Monto Mensuales Merienda;Monto Mensuales Cena;TOTAL;Mes de Pago;Año\n"
    )
    row = (
        f"{comedor_pk};Comedor Prueba;Org X;EX-2024-AAA;EX-2025-BBB;150;0;0;750;"
        "$ 57.450,00;$ 0,00;$ 0,00;$ 572.250,00;$ 629.700,00;septiembre;2025\n"
    )
    return headers + row


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
            "delimiter": ";",
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
    # Captured expediente de pago number in batch
    assert batch.numero_expediente_pago == "EX-2025-BBB"

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
            "delimiter": ";",
            "has_header": True,
        },
    )

    batch = ArchivosImportados.objects.latest("id")

    # Step 2: import
    import_url = reverse("importar_datos", kwargs={"id_archivo": batch.id})
    resp = client_logged.post(import_url)
    assert resp.status_code in (302, 200)

    # One ExpedientePago created
    assert ExpedientePago.objects.count() == 1
    exp = ExpedientePago.objects.first()
    assert exp is not None
    # Check key fields parsed according to new headers
    assert exp.comedor_id == comedor.id
    assert exp.expediente_pago == "EX-2025-BBB"
    assert exp.expediente_convenio == "EX-2024-AAA"
    assert exp.prestaciones_mensuales_desayuno == 150
    assert exp.prestaciones_mensuales_cena == 750
    assert exp.monto_mensual_desayuno == Decimal("57450")
    assert exp.monto_mensual_cena == Decimal("572250")
    assert exp.total == Decimal("629700")
    assert str(exp.mes_pago).lower() == "septiembre"
    assert str(exp.ano) == "2025"

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
        {"file": uploaded, "delimiter": ";", "has_header": True},
    )
    batch = ArchivosImportados.objects.latest("id")

    # First import
    client_logged.post(reverse("importar_datos", kwargs={"id_archivo": batch.id}))
    assert ExpedientePago.objects.count() == 1

    # Second import should not create more
    resp = client_logged.post(
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
    client_logged.post(reverse("importar_datos", kwargs={"id_archivo": batch.id}))
    assert ExpedientePago.objects.count() == 1
    batch.refresh_from_db()
    assert batch.importacion_completada is True

    # Delete imported data
    resp = client_logged.post(
        reverse("borrar_datos_importados", kwargs={"id_archivo": batch.id})
    )
    assert resp.status_code in (302, 200)

    # All imported records removed and flag reset
    assert ExpedientePago.objects.count() == 0
    assert RegistroImportado.objects.count() == 0
    batch.refresh_from_db()
    assert batch.importacion_completada is False
