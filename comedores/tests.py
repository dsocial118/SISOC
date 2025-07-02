from unittest import mock

import pytest
from django.urls import reverse


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
