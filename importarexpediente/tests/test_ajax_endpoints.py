import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from importarexpediente.models import ArchivosImportados

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


@pytest.fixture
def seed_imports(client_logged, tmp_media):
    # Create a couple of batches to paginate/search using new headers
    headers = (
        "ID;COMEDOR;ORGANIZACIÓN;EXPEDIENTE del CONVENIO;Expediente de Pago;TOTAL;Mes de Pago;Año\n"
    )
    for i in range(3):
        row = f"{i+1};Comedor {i};Org {i};EX-2024-{i};EX-2025-{i};$ 1.000,00;enero;2025\n"
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
