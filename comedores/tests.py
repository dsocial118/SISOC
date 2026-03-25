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
from organizaciones.models import Aval, Firmante, Organizacion, RolFirmante


# Tests for ComedorDetailView (HTML)
@pytest.mark.django_db
def test_comedor_detail_view_get_context(client_logged_fixture, comedor_fixture):
    client = client_logged_fixture
    comedor = comedor_fixture
    url = reverse("comedor_detalle", kwargs={"pk": comedor.pk})
    response = client.get(url)
    body = response.content.decode()
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
        "admision",
    ]:
        assert key in response.context

    assert "GESTIONAR_API_KEY" not in response.context
    assert "GESTIONAR_API_CREAR_COMEDOR" not in response.context
    assert "nuevo_comedor_detalle" not in body
    assert "comedores_nuevo/" not in body
    assert reverse("relevamientos", kwargs={"comedor_pk": comedor.pk}) in body
    assert (
        reverse("relevamiento_create_edit_ajax", kwargs={"pk": comedor.pk}) not in body
    )


@pytest.mark.django_db
def test_comedor_detail_view_responsables_usa_datos_de_organizacion(
    client_logged_fixture, comedor_fixture
):
    client = client_logged_fixture
    comedor = comedor_fixture
    organizacion = Organizacion.objects.create(
        nombre="Asociacion Comedor Norte",
        cuit=20333444556,
        email="org@example.com",
        telefono=1144556677,
    )
    rol = RolFirmante.objects.create(nombre="Presidenta")
    Firmante.objects.create(
        organizacion=organizacion,
        nombre="Ana Perez",
        cuit=27111222333,
        rol=rol,
    )
    Firmante.objects.create(
        organizacion=organizacion,
        nombre="Luis Gomez",
        cuit=20222333444,
    )
    Aval.objects.create(
        organizacion=organizacion,
        nombre="Carlos Aval",
        cuit=20999888777,
    )
    comedor.organizacion = organizacion
    comedor.save(update_fields=["organizacion"])

    response = client.get(reverse("comedor_detalle", kwargs={"pk": comedor.pk}))
    body = response.content.decode()

    assert response.status_code == 200
    assert "Asociacion Comedor Norte" in body
    assert "org@example.com" in body
    assert "1144556677" in body
    assert "Firmantes" in body
    assert "Presidenta: Ana Perez 27111222333" in body
    assert "Luis Gomez 20222333444" in body
    assert "Avales" in body
    assert "Aval 1" in body
    assert "Carlos Aval 20999888777" in body
    assert "Responsable 1" not in body
    assert "Responsable 2" not in body
    assert "Responsable de la tarjeta del cobro" not in body
    assert "<strong>Aval 2:</strong>" not in body


@pytest.mark.django_db
def test_comedor_detail_view_responsables_oculta_datos_y_bloques_vacios(
    client_logged_fixture, comedor_fixture
):
    client = client_logged_fixture
    comedor = comedor_fixture
    organizacion = Organizacion.objects.create(
        nombre="Organizacion Minima",
        cuit=20123456789,
        email="",
        telefono=None,
        subtipo_entidad=None,
    )
    comedor.organizacion = organizacion
    comedor.save(update_fields=["organizacion"])

    response = client.get(reverse("comedor_detalle", kwargs={"pk": comedor.pk}))
    body = response.content.decode()

    assert response.status_code == 200
    assert "Organizacion Minima" in body
    assert ">Email:</strong>" not in body
    assert ">Telefono:</strong>" not in body
    assert ">Subtipo de entidad:</strong>" not in body
    assert "Firmantes" not in body
    assert "Avales" not in body


@pytest.mark.django_db
def test_comedor_detalle_legacy_redirect(client_logged_fixture, comedor_fixture):
    client = client_logged_fixture
    comedor = comedor_fixture
    url = reverse("nuevo_comedor_detalle", kwargs={"pk": comedor.pk})
    response = client.get(url)
    assert response.status_code == 301
    assert response.headers["Location"] == reverse(
        "comedor_detalle", kwargs={"pk": comedor.pk}
    )


@pytest.mark.django_db
def test_comedor_detalle_legacy_redirect_preserva_query_string(
    client_logged_fixture, comedor_fixture
):
    client = client_logged_fixture
    comedor = comedor_fixture
    url = reverse("nuevo_comedor_detalle", kwargs={"pk": comedor.pk})
    response = client.get(f"{url}?admision_id=99")
    assert response.status_code == 301
    assert response.headers["Location"] == (
        f"{reverse('comedor_detalle', kwargs={'pk': comedor.pk})}?admision_id=99"
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
def test_comedor_detail_view_post_legacy_relevamiento_redirects_a_relevamientos(
    client_logged_fixture, comedor_fixture
):
    client = client_logged_fixture
    comedor = comedor_fixture
    url = reverse("comedor_detalle", kwargs={"pk": comedor.pk})
    response = client.post(url, {"territorial": "1"}, follow=True)
    assert response.status_code == 200
    assert response.redirect_chain == [
        (reverse("relevamientos", kwargs={"comedor_pk": comedor.pk}), 302)
    ]
    assert (
        "La gestión de relevamientos ya no se realiza desde este legajo."
        in response.content.decode()
    )


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
    monkeypatch.setattr(
        "comedores.views.relevamientos.get_object_or_404",
        mock.Mock(return_value=relevamiento_mock),
    )

    url = reverse("relevamiento_create_edit_ajax", kwargs={"pk": comedor_fixture.pk})
    data = {
        "territorial_editar": "1",
        "relevamiento_id": "1000",
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
    # El registro importado queda en ACTIVO
    nomina_importada = Nomina.objects.get(admision=admision_actual)
    assert nomina_importada.estado == Nomina.ESTADO_ACTIVO


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
def test_nomina_detail_view_filtra_por_dni_en_toda_la_nomina(
    client_nomina_fixture, admision_fixture
):
    """El filtro por DNI debe aplicarse antes de paginar, no solo sobre la página actual."""
    from datetime import date

    ciudadano_objetivo = Ciudadano.objects.create(
        nombre="Persona",
        apellido="Objetivo",
        documento=12345678,
        fecha_nacimiento=date(1990, 1, 1),
    )
    Nomina.objects.create(
        admision=admision_fixture,
        ciudadano=ciudadano_objetivo,
        estado=Nomina.ESTADO_ACTIVO,
    )

    # Crea 100 registros más nuevos para forzar que el objetivo quede fuera de la página 1.
    for idx in range(100):
        ciudadano = Ciudadano.objects.create(
            nombre=f"Persona{idx}",
            apellido=f"Apellido{idx}",
            documento=30000000 + idx,
            fecha_nacimiento=date(1990, 1, 1),
        )
        Nomina.objects.create(
            admision=admision_fixture,
            ciudadano=ciudadano,
            estado=Nomina.ESTADO_ACTIVO,
        )

    comedor = admision_fixture.comedor
    url = reverse(
        "nomina_ver",
        kwargs={"pk": comedor.pk, "admision_pk": admision_fixture.pk},
    )

    response_sin_filtro = client_nomina_fixture.get(url, {"page": 1})
    assert response_sin_filtro.status_code == 200
    assert "12345678" not in response_sin_filtro.content.decode()

    response_filtrada = client_nomina_fixture.get(url, {"page": 1, "dni": "12345678"})
    assert response_filtrada.status_code == 200
    assert "12345678" in response_filtrada.content.decode()
    assert response_filtrada.context["nomina"].paginator.count == 1


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


# ---------------------------------------------------------------------------
# Tests — nómina directa (programas 3/4, sin admisión)
# ---------------------------------------------------------------------------

import csv
import io
from django.core.management import call_command

from comedores.models import Programas
from comedores.views import (
    NominaDirectaDetailView,
    NominaDirectaCreateView,
    NominaDirectaDeleteView,
)


def _programa(pk, nombre):
    """Crea (o recupera) un Programas con ID exacto."""
    prog, _ = Programas.objects.get_or_create(id=pk, defaults={"nombre": nombre})
    return prog


# ---------------------------------------------------------------------------
# Service — agregar ciudadano a nómina directa (prog 3/4)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_agregar_ciudadano_a_nomina_directa_caso_feliz(ciudadano_fixture):
    """Agrega ciudadano a nómina directa de un comedor 3/4 (sin admisión)."""
    prog = _programa(3, "Abordaje comunitario - Línea Secos")
    comedor = Comedor.objects.create(nombre="Comedor Prog 3", programa=prog)

    ok, _msg = ComedorService.agregar_ciudadano_a_nomina(
        ciudadano_id=ciudadano_fixture.pk,
        user=mock.Mock(),
        comedor_id=comedor.pk,
    )

    assert ok is True
    assert Nomina.objects.filter(
        comedor=comedor, ciudadano=ciudadano_fixture, admision__isnull=True
    ).exists()


@pytest.mark.django_db
def test_agregar_ciudadano_ya_en_nomina_directa(ciudadano_fixture):
    """Retorna False si el ciudadano ya está en la nómina directa del comedor."""
    prog = _programa(4, "Abordaje comunitario - Línea Tradicional")
    comedor = Comedor.objects.create(nombre="Comedor Prog 4", programa=prog)
    Nomina.objects.create(
        comedor=comedor,
        ciudadano=ciudadano_fixture,
        estado=Nomina.ESTADO_ACTIVO,
    )

    ok, msg = ComedorService.agregar_ciudadano_a_nomina(
        ciudadano_id=ciudadano_fixture.pk,
        user=mock.Mock(),
        comedor_id=comedor.pk,
    )

    assert ok is False
    assert "ya está en la nómina" in msg


@pytest.mark.django_db
def test_get_nomina_detail_by_comedor_solo_devuelve_nominas_directas(ciudadano_fixture):
    """get_nomina_detail_by_comedor solo incluye nóminas con admision=null del comedor."""
    prog = _programa(3, "Abordaje comunitario - Línea Secos")
    comedor = Comedor.objects.create(nombre="Comedor Detail", programa=prog)
    comedor_otro = Comedor.objects.create(nombre="Comedor Otro", programa=prog)
    admision = Admision.objects.create(comedor=comedor)

    # Nómina directa del comedor (debe aparecer)
    Nomina.objects.create(
        comedor=comedor, ciudadano=ciudadano_fixture, estado=Nomina.ESTADO_ACTIVO
    )
    # Nómina vía admisión del mismo comedor (no debe aparecer)
    Nomina.objects.create(
        admision=admision, ciudadano=ciudadano_fixture, estado=Nomina.ESTADO_ACTIVO
    )
    # Nómina directa de otro comedor (no debe aparecer)
    Nomina.objects.create(
        comedor=comedor_otro, ciudadano=ciudadano_fixture, estado=Nomina.ESTADO_ACTIVO
    )

    _, *_, total, _ = ComedorService.get_nomina_detail_by_comedor(comedor.pk)

    assert total == 1


# ---------------------------------------------------------------------------
# Signal — asignar nóminas directas al crear admisión en comedor 3/4
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_signal_asigna_nominas_directas_al_crear_admision_prog3(ciudadano_fixture):
    """Al crear admisión en comedor prog 3, las nóminas directas pasan a esa admisión."""
    prog = _programa(3, "Abordaje comunitario - Línea Secos")
    comedor = Comedor.objects.create(nombre="Comedor Signal P3", programa=prog)
    Nomina.objects.create(
        comedor=comedor, ciudadano=ciudadano_fixture, estado=Nomina.ESTADO_ACTIVO
    )

    admision = Admision.objects.create(comedor=comedor)

    nomina = Nomina.objects.get(ciudadano=ciudadano_fixture)
    assert nomina.admision_id == admision.pk
    assert nomina.comedor_id is None


@pytest.mark.django_db
def test_signal_asigna_nominas_directas_al_crear_admision_prog4(ciudadano_fixture):
    """Al crear admisión en comedor prog 4, las nóminas directas pasan a esa admisión."""
    prog = _programa(4, "Abordaje comunitario - Línea Tradicional")
    comedor = Comedor.objects.create(nombre="Comedor Signal P4", programa=prog)
    Nomina.objects.create(
        comedor=comedor, ciudadano=ciudadano_fixture, estado=Nomina.ESTADO_ACTIVO
    )

    admision = Admision.objects.create(comedor=comedor)

    nomina = Nomina.objects.get(ciudadano=ciudadano_fixture)
    assert nomina.admision_id == admision.pk
    assert nomina.comedor_id is None


@pytest.mark.django_db
def test_signal_no_asigna_nominas_si_programa_2(ciudadano_fixture):
    """Al crear admisión en comedor prog 2, las nóminas directas NO se tocan."""
    prog = _programa(2, "Alimentar comunidad")
    comedor = Comedor.objects.create(nombre="Comedor Signal P2", programa=prog)
    nomina = Nomina.objects.create(
        comedor=comedor, ciudadano=ciudadano_fixture, estado=Nomina.ESTADO_ACTIVO
    )

    Admision.objects.create(comedor=comedor)

    nomina.refresh_from_db()
    assert nomina.admision_id is None
    assert nomina.comedor_id == comedor.pk


@pytest.mark.django_db
def test_signal_no_asigna_en_update_de_admision(ciudadano_fixture):
    """El signal solo corre al crear admisión, no al actualizarla."""
    prog = _programa(3, "Abordaje comunitario - Línea Secos")
    comedor = Comedor.objects.create(nombre="Comedor Signal Update", programa=prog)
    admision = Admision.objects.create(comedor=comedor)

    # Nómina directa creada DESPUÉS de la admisión
    nomina = Nomina.objects.create(
        comedor=comedor, ciudadano=ciudadano_fixture, estado=Nomina.ESTADO_ACTIVO
    )

    # Update de admisión no debe disparar el signal
    admision.save()

    nomina.refresh_from_db()
    assert nomina.comedor_id == comedor.pk  # sigue sin asignarse
    assert nomina.admision_id is None


# ---------------------------------------------------------------------------
# Vistas — NominaDirecta* (prog 3/4)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_nomina_directa_detail_view_responde_ok(client_nomina_fixture):
    """NominaDirectaDetailView responde 200 con contexto correcto."""
    prog = _programa(3, "Abordaje comunitario - Línea Secos")
    comedor = Comedor.objects.create(nombre="Comedor Vista P3", programa=prog)

    url = reverse("nomina_directa_ver", kwargs={"pk": comedor.pk})
    response = client_nomina_fixture.get(url)

    assert response.status_code == 200
    for key in ["nomina", "cantidad_nomina", "object", "admision_pk"]:
        assert key in response.context
    assert response.context["admision_pk"] is None
    assert response.context["object"].pk == comedor.pk


@pytest.mark.django_db
def test_nomina_directa_detail_view_muestra_solo_nominas_directas(
    client_nomina_fixture, ciudadano_fixture
):
    """NominaDirectaDetailView muestra solo nóminas directas del comedor (admision=null)."""
    prog = _programa(4, "Abordaje comunitario - Línea Tradicional")
    comedor = Comedor.objects.create(nombre="Comedor Vista P4", programa=prog)
    admision = Admision.objects.create(comedor=comedor)
    # Nómina directa (debe aparecer)
    Nomina.objects.create(
        comedor=comedor, ciudadano=ciudadano_fixture, estado=Nomina.ESTADO_ACTIVO
    )
    # Nómina vía admisión (no debe aparecer)
    Nomina.objects.create(
        admision=admision, ciudadano=ciudadano_fixture, estado=Nomina.ESTADO_ACTIVO
    )

    url = reverse("nomina_directa_ver", kwargs={"pk": comedor.pk})
    response = client_nomina_fixture.get(url)

    assert response.status_code == 200
    assert response.context["cantidad_nomina"] == 1


@pytest.mark.django_db
def test_nomina_directa_detail_view_404_comedor_inexistente(client_nomina_fixture):
    """Retorna 404 si el comedor no existe."""
    url = reverse("nomina_directa_ver", kwargs={"pk": 99999})
    response = client_nomina_fixture.get(url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_nomina_directa_detail_view_404_para_programa_con_admision(
    client_nomina_fixture,
):
    """La nómina directa solo aplica a programas 3/4."""
    prog = _programa(2, "Alimentar comunidad")
    comedor = Comedor.objects.create(nombre="Comedor Vista P2", programa=prog)

    url = reverse("nomina_directa_ver", kwargs={"pk": comedor.pk})
    response = client_nomina_fixture.get(url)

    assert response.status_code == 404


@pytest.mark.django_db
def test_nomina_directa_delete_view_muestra_cancelacion_directa(
    client_nomina_fixture, ciudadano_fixture
):
    """La confirmación de baja directa debe volver a la nómina directa."""
    prog = _programa(3, "Abordaje comunitario - Línea Secos")
    comedor = Comedor.objects.create(nombre="Comedor Borrado", programa=prog)
    nomina = Nomina.objects.create(
        comedor=comedor, ciudadano=ciudadano_fixture, estado=Nomina.ESTADO_ACTIVO
    )

    url = reverse("nomina_directa_borrar", kwargs={"pk": comedor.pk, "pk2": nomina.pk})
    response = client_nomina_fixture.get(url)

    assert response.status_code == 200
    assert (
        reverse("nomina_directa_ver", kwargs={"pk": comedor.pk})
        in response.content.decode()
    )


@pytest.mark.django_db
def test_nomina_editar_ajax_funciona_con_nomina_directa(
    client_nomina_fixture, ciudadano_fixture
):
    """nomina_editar_ajax acepta nóminas directas (comedor FK, sin admision)."""
    prog = _programa(3, "Abordaje comunitario - Línea Secos")
    comedor = Comedor.objects.create(nombre="Comedor Ajax", programa=prog)
    nomina = Nomina.objects.create(
        comedor=comedor, ciudadano=ciudadano_fixture, estado=Nomina.ESTADO_ACTIVO
    )

    url = reverse("nomina_editar_ajax", kwargs={"pk": nomina.pk})
    response = client_nomina_fixture.get(url)

    assert response.status_code == 200


@pytest.mark.django_db
def test_nomina_cambiar_estado_funciona_con_nomina_directa(
    client_nomina_fixture, ciudadano_fixture
):
    """nomina_cambiar_estado acepta nóminas directas y cambia el estado."""
    prog = _programa(4, "Abordaje comunitario - Línea Tradicional")
    comedor = Comedor.objects.create(nombre="Comedor Estado", programa=prog)
    nomina = Nomina.objects.create(
        comedor=comedor, ciudadano=ciudadano_fixture, estado=Nomina.ESTADO_ACTIVO
    )

    url = reverse("nomina_cambiar_estado", kwargs={"pk": nomina.pk})
    response = client_nomina_fixture.post(url, {"estado": Nomina.ESTADO_ESPERA})

    assert response.status_code == 200
    nomina.refresh_from_db()
    assert nomina.estado == Nomina.ESTADO_ESPERA


# ---------------------------------------------------------------------------
# Management command — recuperar_nominas_csv
# ---------------------------------------------------------------------------


def _csv_content(rows):
    """Genera contenido CSV con el header del backup real (9 columnas)."""
    header = "id,ciudadano_id,comedor_id,fecha,estado,observaciones,deleted_at,deleted_by_id,admision_id_sugerida"
    lines = [header] + [
        ",".join(
            [
                str(r["id"]),
                str(r["ciudadano_id"]),
                str(r["comedor_id"]),
                "2025-12-16 11:37:56",
                "activo",
                "",  # observaciones
                "",  # deleted_at
                "",  # deleted_by_id
                str(r.get("admision_id_sugerida", "")),
            ]
        )
        for r in rows
    ]
    return "\n".join(lines)


@pytest.mark.django_db
def test_recuperar_nominas_csv_asigna_comedor_prog34(tmp_path, ciudadano_fixture):
    """Para prog 3/4, asigna comedor_id y deja admision=null."""
    prog = _programa(3, "Abordaje comunitario - Línea Secos")
    comedor = Comedor.objects.create(nombre="Comedor CSV P3", programa=prog)
    nomina = Nomina.objects.create(
        ciudadano=ciudadano_fixture, estado=Nomina.ESTADO_ACTIVO
    )

    csv_file = tmp_path / "backup.csv"
    csv_file.write_text(
        _csv_content(
            [
                {
                    "id": nomina.pk,
                    "ciudadano_id": ciudadano_fixture.pk,
                    "comedor_id": comedor.pk,
                }
            ]
        )
    )

    call_command("recuperar_nominas_csv", str(csv_file))

    nomina.refresh_from_db()
    assert nomina.comedor_id == comedor.pk
    assert nomina.admision_id is None


@pytest.mark.django_db
def test_recuperar_nominas_csv_asigna_admision_prog2(tmp_path, ciudadano_fixture):
    """Para prog 2, asigna comedor_id y admision_id desde admision_id_sugerida."""
    prog = _programa(2, "Alimentar comunidad")
    comedor = Comedor.objects.create(nombre="Comedor CSV P2", programa=prog)
    admision = Admision.objects.create(comedor=comedor)
    nomina = Nomina.objects.create(
        ciudadano=ciudadano_fixture, estado=Nomina.ESTADO_ACTIVO
    )

    csv_file = tmp_path / "backup.csv"
    csv_file.write_text(
        _csv_content(
            [
                {
                    "id": nomina.pk,
                    "ciudadano_id": ciudadano_fixture.pk,
                    "comedor_id": comedor.pk,
                    "admision_id_sugerida": admision.pk,
                }
            ]
        )
    )

    call_command("recuperar_nominas_csv", str(csv_file))

    nomina.refresh_from_db()
    assert nomina.comedor_id == comedor.pk
    assert nomina.admision_id == admision.pk


@pytest.mark.django_db
def test_recuperar_nominas_csv_dry_run_no_modifica(tmp_path, ciudadano_fixture):
    """Con --dry-run, no se aplica ningún cambio a la BD."""
    prog = _programa(3, "Abordaje comunitario - Línea Secos")
    comedor = Comedor.objects.create(nombre="Comedor DryRun", programa=prog)
    nomina = Nomina.objects.create(
        ciudadano=ciudadano_fixture, estado=Nomina.ESTADO_ACTIVO
    )

    csv_file = tmp_path / "backup.csv"
    csv_file.write_text(
        _csv_content(
            [
                {
                    "id": nomina.pk,
                    "ciudadano_id": ciudadano_fixture.pk,
                    "comedor_id": comedor.pk,
                }
            ]
        )
    )

    call_command("recuperar_nominas_csv", str(csv_file), "--dry-run")

    nomina.refresh_from_db()
    assert nomina.comedor_id is None  # sin cambios


@pytest.mark.django_db
def test_recuperar_nominas_csv_omite_comedor_no_encontrado(tmp_path, ciudadano_fixture):
    """Si el comedor_id del CSV no existe en la BD, la nómina queda sin cambios."""
    nomina = Nomina.objects.create(
        ciudadano=ciudadano_fixture, estado=Nomina.ESTADO_ACTIVO
    )

    csv_file = tmp_path / "backup.csv"
    csv_file.write_text(
        _csv_content(
            [
                {
                    "id": nomina.pk,
                    "ciudadano_id": ciudadano_fixture.pk,
                    "comedor_id": 99999,
                }
            ]
        )
    )

    call_command("recuperar_nominas_csv", str(csv_file))

    nomina.refresh_from_db()
    assert nomina.comedor_id is None


@pytest.mark.django_db
def test_recuperar_nominas_csv_incluye_soft_deleted(tmp_path, ciudadano_fixture):
    """El command procesa también las nóminas soft-deleted (all_objects)."""
    from django.utils import timezone

    prog = _programa(3, "Abordaje comunitario - Línea Secos")
    comedor = Comedor.objects.create(nombre="Comedor SoftDel", programa=prog)
    nomina = Nomina.objects.create(
        ciudadano=ciudadano_fixture,
        estado=Nomina.ESTADO_BAJA,
        deleted_at=timezone.now(),
    )

    csv_file = tmp_path / "backup.csv"
    csv_file.write_text(
        _csv_content(
            [
                {
                    "id": nomina.pk,
                    "ciudadano_id": ciudadano_fixture.pk,
                    "comedor_id": comedor.pk,
                }
            ]
        )
    )

    call_command("recuperar_nominas_csv", str(csv_file))

    nomina_actualizada = Nomina.all_objects.get(pk=nomina.pk)
    assert nomina_actualizada.comedor_id == comedor.pk


def test_comedores_views_exporta_vistas_directas():
    """comedores.views expone las tres vistas de nómina directa."""
    assert NominaDirectaDetailView.__name__ == "NominaDirectaDetailView"
    assert NominaDirectaCreateView.__name__ == "NominaDirectaCreateView"
    assert NominaDirectaDeleteView.__name__ == "NominaDirectaDeleteView"
