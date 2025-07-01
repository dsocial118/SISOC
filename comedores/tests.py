import threading
from unittest import mock

import factory
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client
from django.urls import reverse
from faker import Faker

from comedores.models import Comedor

fake = Faker()


class ComedorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Comedor

    nombre = factory.LazyAttribute(lambda _: fake.company())


@pytest.fixture
def user_fixture(db):
    user_model = get_user_model()
    user_instance = user_model.objects.create_user(username=fake.user_name(), password="testpass")
    for group_name in [
        "Comedores Ver",
        "Comedores Relevamiento Ver",
        "Comedores Relevamiento Crear",
        "Comedores Relevamiento Detalle",
        "Comedores Relevamiento Editar",
    ]:
        group, _ = Group.objects.get_or_create(name=group_name)
        user_instance.groups.add(group)
    user_instance.save()
    return user_instance


@pytest.fixture
def client_logged_fixture(user_fixture):
    client = Client()
    client.login(username=user_fixture.username, password="testpass")
    return client


@pytest.fixture
def comedor_fixture(db):
    return ComedorFactory()


@pytest.fixture(autouse=True)
def monkeypatch_comedor_detail_services(monkeypatch, comedor_fixture):
    monkeypatch.setattr(
        "comedores.services.comedor_service.ComedorService.get_comedor_detail_object",
        lambda pk: comedor_fixture,
    )
    monkeypatch.setattr(
        "comedores.services.comedor_service.ComedorService.get_presupuestos",
        lambda pk: (10, 1, 2, 3, 4),
    )
    monkeypatch.setattr(
        "rendicioncuentasmensual.services.RendicionCuentaMensualService.cantidad_rendiciones_cuentas_mensuales",
        lambda obj: 5,
    )
    monkeypatch.setattr(comedor_fixture.relevamiento_set, "order_by", lambda *a, **kw: [])
    monkeypatch.setattr(comedor_fixture.relevamiento_set, "count", lambda: 1)
    monkeypatch.setattr(comedor_fixture.observacion_set, "order_by", lambda *a, **kw: [])
    monkeypatch.setattr(comedor_fixture.imagenes, "values", lambda *a, **kw: [])
    monkeypatch.setattr(
        comedor_fixture.clasificacioncomedor_set.order_by(), "first", lambda: None
    )
    monkeypatch.setattr(comedor_fixture.admision_set, "first", lambda: None)
    monkeypatch.setattr(
        "configuraciones.templatetags.custom_filters.has_group",
        lambda user, group: (
            False
            if user is None
            else (
                    hasattr(user, "groups")
                    and (
                            user.groups.filter(name=group).exists()
                            or getattr(user, "is_superuser", False)
                    )
            )
        ),
    )
    monkeypatch.setattr(threading.Thread, "start", lambda self: None)
    return comedor_fixture


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
def test_comedor_detail_view_post_new_relevamiento(client_logged_fixture, comedor_fixture, monkeypatch):
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
def test_comedor_detail_view_post_edit_relevamiento(client_logged_fixture, comedor_fixture, monkeypatch):
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
def test_comedor_detail_view_post_redirects_on_other(client_logged_fixture, comedor_fixture):
    client = client_logged_fixture
    comedor = comedor_fixture
    url = reverse("comedor_detalle", kwargs={"pk": comedor.pk})
    response = client.post(url, {"foo": "bar"})
    assert response.status_code == 302
    assert reverse("comedor_detalle", kwargs={"pk": comedor.pk}) in response.url


@pytest.mark.django_db
def test_comedor_detail_view_post_error(monkeypatch, client_logged_fixture, comedor_fixture):
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
