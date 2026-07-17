"""Tests for test ajax endpoints."""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from comedores.models import Comedor
from importarexpediente.models import ArchivosImportados, ErroresImportacion

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def user(db):
    return User.objects.create_user(username="tester", password="pass1234")


@pytest.fixture
def client_logged(client, user):
    user.user_permissions.add(
        Permission.objects.get(
            content_type__app_label="importarexpediente",
            codename="view_archivosimportados",
        )
    )
    client.login(username="tester", password="pass1234")
    return client


@pytest.fixture
def tmp_media(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
    return settings.MEDIA_ROOT


@pytest.fixture
def seed_imports(client_logged, tmp_media):
    # Create a couple of batches to paginate/search using new headers
    headers = "ID;COMEDOR;ORGANIZACIÃƒÆ’Ã¢â‚¬Å“N;EXPEDIENTE del CONVENIO;Expediente de Pago;TOTAL;Mes de Pago;AÃ±o\n"
    for i in range(3):
        row = (
            f"{i+1};Comedor {i};Org {i};EX-2024-{i};EX-2025-{i};$ 1.000,00;enero;2025\n"
        )
        content = headers + row
        uploaded = SimpleUploadedFile(
            f"expedientes_{i}.csv", content.encode("utf-8"), content_type="text/csv"
        )
        client_logged.post(
            reverse("upload"),
            {"file": uploaded, "delimiter": ";", "has_header": True},
        )
    assert ArchivosImportados.objects.count() >= 3


def test_list_view_and_ajax_filters(client_logged, seed_imports):
    # List view loads (accept redirect or 200 depending on middleware)
    list_url = reverse("importarexpedientes_list")
    resp = client_logged.get(list_url)
    assert resp.status_code in (200, 302)

    # AJAX endpoint returns JSON shape
    ajax_url = reverse("importarexpedientes_ajax")
    resp = client_logged.get(ajax_url, {"busqueda": "expedientes_1.csv"})
    assert resp.status_code == 200
    data = resp.json()
    assert {"html", "pagination_html", "count", "current_page", "total_pages"} <= set(
        data.keys()
    )
    assert "expedientes_1.csv" in data["html"]
    assert "Descargar" in data["html"]


def test_list_and_ajax_require_view_permission(client, user):
    client.force_login(user)

    list_response = client.get(reverse("importarexpedientes_list"))
    ajax_response = client.get(reverse("importarexpedientes_ajax"))

    assert list_response.status_code == 403
    assert ajax_response.status_code == 403


def test_list_view_backfills_periodo_from_stored_file(client_logged, tmp_media):
    content = (
        "ID;COMEDOR;EXPEDIENTE del CONVENIO;Expediente de Pago;TOTAL;Mes de Pago;A\u00f1o de pago\n"
        "1;Comedor;EX-2024-1;EX-2025-OLD;$ 1.000,00;septiembre;2025\n"
    )
    uploaded = SimpleUploadedFile(
        "old.csv",
        content.encode("utf-8"),
        content_type="text/csv",
    )
    batch = ArchivosImportados.objects.create(
        archivo=uploaded,
        delimiter=";",
        usuario=User.objects.get(username="tester"),
    )

    resp = client_logged.get(reverse("importarexpedientes_list"))

    assert resp.status_code == 200
    assert "09/2025" in resp.content.decode()
    batch.refresh_from_db()
    assert batch.periodo_pago == "09/2025"


def test_list_view_backfills_periodo_from_imported_record(client_logged, tmp_media):
    comedor = Comedor.objects.create(nombre="Comedor Periodo Importado")
    batch = ArchivosImportados.objects.create(
        archivo="importados/sin_periodo.csv",
        usuario=User.objects.get(username="tester"),
    )
    exito = batch.exitos.create(fila=2, mensaje="Importado")
    expediente = comedor.expedientes_pagos.create(
        expediente_convenio="EX-2024-IMP",
        expediente_pago="EX-2025-IMP",
        mes_pago="8",
        ano="2025",
        prestaciones_mensuales_desayuno=0,
        prestaciones_mensuales_almuerzo=0,
        prestaciones_mensuales_merienda=0,
        prestaciones_mensuales_cena=0,
        monto_mensual_desayuno=0,
        monto_mensual_almuerzo=0,
        monto_mensual_merienda=0,
        monto_mensual_cena=0,
    )
    exito.registros.create(expediente_pago=expediente)

    resp = client_logged.get(reverse("importarexpedientes_list"))

    assert resp.status_code == 200
    assert "08/2025" in resp.content.decode()
    batch.refresh_from_db()
    assert batch.periodo_pago == "08/2025"


def test_download_imported_file(client_logged, seed_imports):
    batch = ArchivosImportados.objects.latest("id")

    resp = client_logged.get(
        reverse("descargar_archivo_importado", kwargs={"id_archivo": batch.id})
    )

    assert resp.status_code == 200
    assert resp["Content-Disposition"].startswith("attachment;")


def test_detail_view_and_ajax(client_logged, seed_imports):
    batch = ArchivosImportados.objects.latest("id")

    # Detail page
    detail_url = reverse("importarexpediente_detail", kwargs={"id_archivo": batch.id})
    resp = client_logged.get(detail_url)
    assert resp.status_code == 200
    # Context has counters
    assert resp.context["error_count"] >= 0
    assert resp.context["exito_count"] >= 0

    # Detail AJAX
    detail_ajax = reverse(
        "importarexpediente_detail_ajax", kwargs={"id_archivo": batch.id}
    )
    r = client_logged.get(detail_ajax, {"busqueda": "Fila"})
    assert r.status_code == 200
    data = r.json()
    assert {"html", "pagination_html", "count", "current_page", "total_pages"} <= set(
        data.keys()
    )


def test_user_can_list_and_interact_with_another_users_import(client_logged, tmp_media):
    owner = User.objects.create_user(username="owner", password="pass1234")
    uploaded = SimpleUploadedFile(
        "importacion_ajena.csv",
        b"contenido invalido",
        content_type="text/csv",
    )
    batch = ArchivosImportados.objects.create(archivo=uploaded, usuario=owner)
    ErroresImportacion.objects.create(
        archivo_importado=batch,
        fila=2,
        mensaje="Error de prueba",
    )

    list_response = client_logged.get(reverse("importarexpedientes_list"))
    assert list_response.status_code == 200
    assert "importacion_ajena.csv" in list_response.content.decode()
    assert "owner" in list_response.content.decode()

    ajax_response = client_logged.get(
        reverse("importarexpedientes_ajax"), {"busqueda": "owner"}
    )
    assert ajax_response.status_code == 200
    assert ajax_response.json()["count"] == 1
    assert "importacion_ajena.csv" in ajax_response.json()["html"]

    detail_response = client_logged.get(
        reverse("importarexpediente_detail", kwargs={"id_archivo": batch.id})
    )
    assert detail_response.status_code == 200

    detail_ajax_response = client_logged.get(
        reverse("importarexpediente_detail_ajax", kwargs={"id_archivo": batch.id})
    )
    assert detail_ajax_response.status_code == 200
    assert "Error de prueba" in detail_ajax_response.json()["html"]

    download_response = client_logged.get(
        reverse("descargar_archivo_importado", kwargs={"id_archivo": batch.id})
    )
    assert download_response.status_code == 200

    import_response = client_logged.post(
        reverse("importar_datos", kwargs={"id_archivo": batch.id})
    )
    assert import_response.status_code == 302

    delete_response = client_logged.post(
        reverse("borrar_datos_importados", kwargs={"id_archivo": batch.id})
    )
    assert delete_response.status_code == 302
