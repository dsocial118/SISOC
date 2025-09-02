from unittest import mock

import pytest
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.core.files.storage import FileSystemStorage

from comedores.models import Comedor
from comedores.services.comedor_service import ComedorService


# Tests for ComedorDetailView (HTML)
@pytest.mark.django_db
def test_comedor_detail_view_get_context(client_logged_fixture, comedor_fixture):
    client = client_logged_fixture
    comedor = comedor_fixture
    url = reverse("comedor_detalle", kwargs={"pk": comedor.pk})
    response = client.get(url)
    assert response.status_code == 200
    for key in [
        "relevamientos",
        "observaciones",
        "count_relevamientos",
        "count_beneficiarios",
        "presupuesto_desayuno",
        "presupuesto_almuerzo",
        "presupuesto_merienda",
        "presupuesto_cena",
        "imagenes",
        "comedor_categoria",
        "rendicion_cuentas_final_activo",
        "GESTIONAR_API_KEY",
        "GESTIONAR_API_CREAR_COMEDOR",
        "admision",
    ]:
        assert key in response.context


@pytest.mark.django_db
def test_comedor_detail_view_post_new_relevamiento(
    client_logged_fixture, comedor_fixture, monkeypatch
):
    client = client_logged_fixture
    comedor = comedor_fixture
    relevamiento_mock = mock.Mock()
    relevamiento_mock.pk = 1
    relevamiento_mock.comedor.pk = comedor.pk
    monkeypatch.setattr(
        "relevamientos.service.RelevamientoService.create_pendiente",
        lambda req, pk: relevamiento_mock,
    )
    url = reverse("comedor_detalle", kwargs={"pk": comedor.pk})
    response = client.post(url, {"territorial": "1"})
    assert response.status_code == 302
    assert (
        reverse("relevamiento_detalle", kwargs={"pk": 1, "comedor_pk": comedor.pk})
        in response.url
    )


@pytest.mark.django_db
def test_comedor_detail_view_post_edit_relevamiento(
    client_logged_fixture, comedor_fixture, monkeypatch
):
    client = client_logged_fixture
    comedor = comedor_fixture
    relevamiento_mock = mock.Mock()
    relevamiento_mock.pk = 2
    relevamiento_mock.comedor.pk = comedor.pk
    monkeypatch.setattr(
        "relevamientos.service.RelevamientoService.update_territorial",
        lambda req: relevamiento_mock,
    )
    url = reverse("comedor_detalle", kwargs={"pk": comedor.pk})
    response = client.post(url, {"territorial_editar": "1"})
    assert response.status_code == 302
    assert (
        reverse("relevamiento_detalle", kwargs={"pk": 2, "comedor_pk": comedor.pk})
        in response.url
    )


@pytest.mark.django_db
def test_comedor_detail_view_post_redirects_on_other(
    client_logged_fixture, comedor_fixture
):
    client = client_logged_fixture
    comedor = comedor_fixture
    url = reverse("comedor_detalle", kwargs={"pk": comedor.pk})
    response = client.post(url, {"foo": "bar"})
    assert response.status_code == 302
    assert reverse("comedor_detalle", kwargs={"pk": comedor.pk}) in response.url


@pytest.mark.django_db
def test_comedor_detail_view_post_error(
    monkeypatch, client_logged_fixture, comedor_fixture
):
    client = client_logged_fixture
    comedor = comedor_fixture

    def raise_exc(*a, **kw):
        raise RuntimeError("fail")

    monkeypatch.setattr(
        "relevamientos.service.RelevamientoService.create_pendiente", raise_exc
    )
    url = reverse("comedor_detalle", kwargs={"pk": comedor.pk})
    response = client.post(url, {"territorial": "1"}, follow=True)
    assert response.status_code == 200
    assert "Error al crear el relevamiento" in response.content.decode()


# Tests for AJAX endpoint (if present)
@pytest.mark.django_db
def test_relevamiento_create_edit_ajax_crear(
    client_logged_fixture, comedor_fixture, monkeypatch
):
    """
    Prueba la creación de un nuevo relevamiento vía AJAX.
    Verifica que:
    1. Se invoque al servicio correcto
    2. Se retorne la URL de redirección adecuada
    3. El código de estado sea 200
    """
    # Mock del servicio de relevamiento para evitar llamadas reales durante el test
    relevamiento_mock = mock.Mock()
    relevamiento_mock.pk = 999
    relevamiento_mock.comedor = mock.Mock()
    relevamiento_mock.comedor.pk = comedor_fixture.pk

    monkeypatch.setattr(
        "relevamientos.service.RelevamientoService.create_pendiente",
        mock.Mock(return_value=relevamiento_mock),
    )

    url = reverse("relevamiento_create_edit_ajax", kwargs={"pk": comedor_fixture.pk})
    data = {
        "territorial": "1",
    }
    response = client_logged_fixture.post(
        url, data, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
    )

    assert response.status_code == 200
    json_response = response.json()
    assert "url" in json_response
    # Verificar que la URL tenga el formato correcto con los IDs esperados
    expected_url = (
        f"/comedores/{comedor_fixture.pk}/relevamiento/{relevamiento_mock.pk}"
    )
    assert json_response["url"] == expected_url


@pytest.mark.django_db
def test_relevamiento_create_edit_ajax_editar(
    client_logged_fixture, comedor_fixture, monkeypatch
):
    """
    Prueba la edición de un relevamiento vía AJAX.
    Verifica que:
    1. Se invoque al servicio correcto
    2. Se retorne la URL de redirección adecuada
    3. El código de estado sea 200
    """
    relevamiento_mock = mock.Mock()
    relevamiento_mock.pk = 1000
    relevamiento_mock.comedor = mock.Mock()
    relevamiento_mock.comedor.pk = comedor_fixture.pk

    monkeypatch.setattr(
        "relevamientos.service.RelevamientoService.update_territorial",
        mock.Mock(return_value=relevamiento_mock),
    )

    url = reverse("relevamiento_create_edit_ajax", kwargs={"pk": comedor_fixture.pk})
    data = {
        "territorial_editar": "1",
    }
    response = client_logged_fixture.post(
        url, data, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
    )

    assert response.status_code == 200
    json_response = response.json()
    assert "url" in json_response
    # Verificar que la URL tenga el formato correcto con los IDs esperados
    expected_url = (
        f"/comedores/{comedor_fixture.pk}/relevamiento/{relevamiento_mock.pk}"
    )
    assert json_response["url"] == expected_url


@pytest.mark.django_db
def test_relevamiento_create_edit_ajax_accion_invalida(
    client_logged_fixture, comedor_fixture
):
    """
    Prueba que una acción inválida retorne un error.
    """
    url = reverse("relevamiento_create_edit_ajax", kwargs={"pk": comedor_fixture.pk})
    data = {"accion_invalida": "1"}
    response = client_logged_fixture.post(
        url, data, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
    )

    assert response.status_code == 400
    json_response = response.json()
    assert "error" in json_response
    assert "Acción no reconocida" in json_response["error"]


@pytest.mark.django_db
def test_relevamiento_create_edit_ajax_error(
    client_logged_fixture, comedor_fixture, monkeypatch
):
    """
    Prueba el manejo de errores durante la creación/edición.
    """
    monkeypatch.setattr(
        "relevamientos.service.RelevamientoService.create_pendiente",
        mock.Mock(side_effect=Exception("Error inesperado")),
    )

    url = reverse("relevamiento_create_edit_ajax", kwargs={"pk": comedor_fixture.pk})
    data = {
        "territorial": "1",
    }
    response = client_logged_fixture.post(
        url, data, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
    )

    assert response.status_code == 500
    json_response = response.json()
    assert "error" in json_response
    assert "Error inesperado" in json_response["error"]


@pytest.mark.django_db
def test_borrar_foto_legajo_elimina_archivo_y_campo(tmp_path, monkeypatch):
    fs = FileSystemStorage(location=tmp_path)
    with override_settings(MEDIA_ROOT=tmp_path):
        monkeypatch.setattr("comedores.services.comedor_service.default_storage", fs)
        archivo = SimpleUploadedFile(
            "test.jpg", b"contenido", content_type="image/jpeg"
        )
        comedor = Comedor.objects.create(nombre="Prueba", foto_legajo=archivo)
        ruta = comedor.foto_legajo.name
        assert fs.exists(ruta)

        ComedorService.delete_legajo_photo({"foto_legajo_borrar": "1"}, comedor)
        comedor.refresh_from_db()

        assert comedor.foto_legajo is None
        assert not fs.exists(ruta)
