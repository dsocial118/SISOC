"""Tests for tests."""

from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import RequestFactory, override_settings
from django.urls import reverse
from django.utils.html import escape

from comedores.models import Comedor, HistorialValidacion
from comedores.services.comedor_service import ComedorService
from comedores.services.validacion_service import ValidacionService
from comedores.views import ComedorDetailView


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
        "monto_prestacion_mensual",
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
def test_validar_comedor_rollback_on_historial_error(monkeypatch):
    user_model = get_user_model()
    user = user_model.objects.create_superuser(
        username="validator",
        email="validator@example.com",
        password="strong-password",
    )
    comedor = Comedor.objects.create(nombre="Comedor Atomic Test")

    def _raise_integrity_error(*args, **kwargs):
        raise IntegrityError("boom")

    monkeypatch.setattr(
        "comedores.services.validacion_service.HistorialValidacion.objects.create",
        _raise_integrity_error,
    )

    with pytest.raises(IntegrityError):
        ValidacionService.validar_comedor(
            comedor_id=comedor.pk,
            user=user,
            accion="validar",
            comentario="comentario de prueba",
        )

    comedor.refresh_from_db()
    assert comedor.estado_validacion == "Pendiente"
    assert comedor.fecha_validado is None


@pytest.mark.django_db
def test_get_relaciones_optimizadas_escapes_historial_comment():
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username="historial-user",
        email="historial@example.com",
        password="complex-pass",
    )
    comedor = Comedor.objects.create(nombre="Comedor Sanitized")
    HistorialValidacion.objects.create(
        comedor=comedor,
        usuario=user,
        estado_validacion="Validado",
        comentario="<script>alert('xss')</script>",
    )

    view = ComedorDetailView()
    view.request = RequestFactory().get("/comedores/1/")
    view.object = comedor

    relaciones = view.get_relaciones_optimizadas()
    comentario_cell = relaciones["validaciones_items"][0]["cells"][4]["content"]
    estado_cell = relaciones["validaciones_items"][0]["cells"][2]["content"]

    assert comentario_cell == escape("<script>alert('xss')</script>")
    assert str(estado_cell) == '<span class="badge bg-success">Validado</span>'


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
    assert "Error interno" in json_response["error"]


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

        assert not comedor.foto_legajo
        assert not fs.exists(ruta)
