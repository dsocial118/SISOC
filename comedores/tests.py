"""Tests for tests."""

from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import Client, RequestFactory, override_settings
from django.urls import reverse
from django.utils.html import escape

from admisiones.models.admisiones import Admision
from ciudadanos.models import Ciudadano
from comedores.models import Comedor, HistorialValidacion, Nomina
from comedores.services.comedor_service import ComedorService
from comedores.services.validacion_service import ValidacionService
from comedores.views import ComedorDetailView, NominaImportarView


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
        "comedores.models.HistorialValidacion.objects.create",
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
        monkeypatch.setattr(
            "comedores.services.comedor_service.impl.default_storage", fs
        )
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


# ---------------------------------------------------------------------------
# Fixtures para tests de nómina
# ---------------------------------------------------------------------------


@pytest.fixture
def client_nomina_fixture(db):
    """Cliente autenticado con permisos de nómina."""
    user_model = get_user_model()
    user = user_model.objects.create_user(username="nomina_user", password="testpass")
    for group_name in [
        "Comedores Nomina Ver",
        "Comedores Nomina Crear",
        "Comedores Nomina Editar",
        "Comedores Nomina Borrar",
    ]:
        group, _ = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)
    client = Client()
    client.login(username="nomina_user", password="testpass")
    return client


@pytest.fixture
def admision_fixture(db):
    """Comedor + Admisión activa mínima para tests de nómina."""
    comedor = Comedor.objects.create(nombre="Comedor Test Nómina")
    admision = Admision.objects.create(comedor=comedor)
    return admision


@pytest.fixture
def ciudadano_fixture(db):
    """Ciudadano mínimo para tests de nómina."""
    from datetime import date

    return Ciudadano.objects.create(
        nombre="Juan",
        apellido="Test",
        fecha_nacimiento=date(1990, 1, 1),
    )


# ---------------------------------------------------------------------------
# Tests de servicios
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_agregar_ciudadano_a_nomina_caso_feliz(admision_fixture, ciudadano_fixture):
    """Agrega un ciudadano a la nómina de una admisión correctamente."""
    ok, _msg = ComedorService.agregar_ciudadano_a_nomina(
        admision_id=admision_fixture.pk,
        ciudadano_id=ciudadano_fixture.pk,
        user=mock.Mock(),
        estado=Nomina.ESTADO_ACTIVO,
    )

    assert ok is True
    assert Nomina.objects.filter(
        admision=admision_fixture, ciudadano=ciudadano_fixture
    ).exists()


@pytest.mark.django_db
def test_agregar_ciudadano_ya_en_nomina(admision_fixture, ciudadano_fixture):
    """Retorna False si el ciudadano ya está en la nómina de esa admisión."""
    Nomina.objects.create(
        admision=admision_fixture,
        ciudadano=ciudadano_fixture,
        estado=Nomina.ESTADO_ACTIVO,
    )

    ok, msg = ComedorService.agregar_ciudadano_a_nomina(
        admision_id=admision_fixture.pk,
        ciudadano_id=ciudadano_fixture.pk,
        user=mock.Mock(),
    )

    assert ok is False
    assert "ya está en la nómina" in msg


@pytest.mark.django_db
def test_importar_nomina_ultimo_convenio_caso_feliz(ciudadano_fixture):
    """Copia los registros de nómina de la admisión anterior a la actual."""
    comedor = Comedor.objects.create(nombre="Comedor Importar")
    admision_anterior = Admision.objects.create(comedor=comedor)
    admision_actual = Admision.objects.create(comedor=comedor)
    Nomina.objects.create(
        admision=admision_anterior,
        ciudadano=ciudadano_fixture,
        estado=Nomina.ESTADO_ACTIVO,
    )

    ok, _msg, cantidad = ComedorService.importar_nomina_ultimo_convenio(
        admision_id=admision_actual.pk,
        comedor_id=comedor.pk,
    )

    assert ok is True
    assert cantidad == 1
    assert Nomina.objects.filter(
        admision=admision_actual, ciudadano=ciudadano_fixture
    ).exists()
    # El registro importado queda en PENDIENTE
    nomina_importada = Nomina.objects.get(admision=admision_actual)
    assert nomina_importada.estado == Nomina.ESTADO_PENDIENTE


@pytest.mark.django_db
def test_importar_nomina_sin_convenio_anterior_con_nomina():
    """Retorna False si no hay admisión anterior con nómina."""
    comedor = Comedor.objects.create(nombre="Comedor Sin Anterior")
    admision_actual = Admision.objects.create(comedor=comedor)

    ok, _msg, cantidad = ComedorService.importar_nomina_ultimo_convenio(
        admision_id=admision_actual.pk,
        comedor_id=comedor.pk,
    )

    assert ok is False
    assert cantidad == 0


@pytest.mark.django_db
def test_importar_nomina_evita_duplicados(ciudadano_fixture):
    """No duplica personas que ya están en la nómina destino."""
    comedor = Comedor.objects.create(nombre="Comedor Duplicados")
    admision_anterior = Admision.objects.create(comedor=comedor)
    admision_actual = Admision.objects.create(comedor=comedor)
    # El ciudadano está en ambas admisiones
    Nomina.objects.create(
        admision=admision_anterior,
        ciudadano=ciudadano_fixture,
        estado=Nomina.ESTADO_ACTIVO,
    )
    Nomina.objects.create(
        admision=admision_actual,
        ciudadano=ciudadano_fixture,
        estado=Nomina.ESTADO_ACTIVO,
    )

    ok, _msg, cantidad = ComedorService.importar_nomina_ultimo_convenio(
        admision_id=admision_actual.pk,
        comedor_id=comedor.pk,
    )

    assert ok is True
    assert cantidad == 0  # nada nuevo importado
    assert Nomina.objects.filter(admision=admision_actual).count() == 1


@pytest.mark.django_db
def test_importar_nomina_toma_admision_anterior_y_no_una_posterior():
    """Importa desde la admisión anterior real, no desde una más nueva."""
    from datetime import date

    comedor = Comedor.objects.create(nombre="Comedor Orden")
    admision_vieja = Admision.objects.create(comedor=comedor)
    admision_destino = Admision.objects.create(comedor=comedor)
    admision_mas_nueva = Admision.objects.create(comedor=comedor)

    ciudadano_viejo = Ciudadano.objects.create(
        nombre="Ana",
        apellido="Vieja",
        fecha_nacimiento=date(1990, 1, 1),
    )
    ciudadano_nuevo = Ciudadano.objects.create(
        nombre="Beto",
        apellido="Nuevo",
        fecha_nacimiento=date(1991, 1, 1),
    )
    Nomina.objects.create(admision=admision_vieja, ciudadano=ciudadano_viejo)
    Nomina.objects.create(admision=admision_mas_nueva, ciudadano=ciudadano_nuevo)

    ok, _msg, cantidad = ComedorService.importar_nomina_ultimo_convenio(
        admision_id=admision_destino.pk,
        comedor_id=comedor.pk,
    )

    assert ok is True
    assert cantidad == 1
    assert Nomina.objects.filter(
        admision=admision_destino, ciudadano=ciudadano_viejo
    ).exists()
    assert not Nomina.objects.filter(
        admision=admision_destino, ciudadano=ciudadano_nuevo
    ).exists()


@pytest.mark.django_db
def test_importar_nomina_falla_si_admision_no_corresponde_al_comedor():
    """Retorna error si la admisión destino no pertenece al comedor recibido."""
    comedor_a = Comedor.objects.create(nombre="Comedor A")
    comedor_b = Comedor.objects.create(nombre="Comedor B")
    admision_b = Admision.objects.create(comedor=comedor_b)

    ok, msg, cantidad = ComedorService.importar_nomina_ultimo_convenio(
        admision_id=admision_b.pk,
        comedor_id=comedor_a.pk,
    )

    assert ok is False
    assert "no corresponde al comedor" in msg
    assert cantidad == 0


# ---------------------------------------------------------------------------
# Tests de vistas
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_nomina_detail_view_responde_ok(client_nomina_fixture, admision_fixture):
    """NominaDetailView responde 200 y tiene las claves de contexto esperadas."""
    comedor = admision_fixture.comedor
    url = reverse(
        "nomina_ver",
        kwargs={"pk": comedor.pk, "admision_pk": admision_fixture.pk},
    )
    response = client_nomina_fixture.get(url)

    assert response.status_code == 200
    for key in ["nomina", "cantidad_nomina", "object", "admision_pk"]:
        assert key in response.context


@pytest.mark.django_db
def test_nomina_detail_view_404_si_admision_no_corresponde(client_nomina_fixture):
    """Retorna 404 si la admisión no pertenece al comedor de la URL."""
    comedor_a = Comedor.objects.create(nombre="Comedor A")
    comedor_b = Comedor.objects.create(nombre="Comedor B")
    admision_b = Admision.objects.create(comedor=comedor_b)

    url = reverse(
        "nomina_ver",
        kwargs={"pk": comedor_a.pk, "admision_pk": admision_b.pk},
    )
    response = client_nomina_fixture.get(url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_nomina_importar_view_redirige(
    client_nomina_fixture, admision_fixture, ciudadano_fixture
):
    """POST a NominaImportarView redirige a nomina_ver."""
    comedor = admision_fixture.comedor
    admision_nueva = Admision.objects.create(comedor=comedor)
    # Hay nómina en la admisión anterior para poder importar
    Nomina.objects.create(
        admision=admision_fixture,
        ciudadano=ciudadano_fixture,
        estado=Nomina.ESTADO_ACTIVO,
    )

    url = reverse(
        "nomina_importar",
        kwargs={"pk": comedor.pk, "admision_pk": admision_nueva.pk},
    )
    response = client_nomina_fixture.post(url)

    assert response.status_code == 302
    expected_redirect = reverse(
        "nomina_ver",
        kwargs={"pk": comedor.pk, "admision_pk": admision_nueva.pk},
    )
    assert expected_redirect in response.url


@pytest.mark.django_db
def test_nomina_importar_view_404_si_admision_no_corresponde(client_nomina_fixture):
    """Retorna 404 si la admisión no corresponde al comedor en la URL."""
    comedor_a = Comedor.objects.create(nombre="Comedor A")
    comedor_b = Comedor.objects.create(nombre="Comedor B")
    admision_b = Admision.objects.create(comedor=comedor_b)

    url = reverse(
        "nomina_importar",
        kwargs={"pk": comedor_a.pk, "admision_pk": admision_b.pk},
    )
    response = client_nomina_fixture.post(url)
    assert response.status_code == 404


def test_comedores_views_exporta_nomina_importar_view():
    """`comedores.views` expone NominaImportarView para imports de URLs."""
    assert NominaImportarView.__name__ == "NominaImportarView"
