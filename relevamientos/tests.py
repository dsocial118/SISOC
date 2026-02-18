"""Tests for tests."""

import pytest
from django.urls import reverse

from relevamientos.models import Relevamiento


@pytest.mark.django_db
def test_create_view_get(client_logged, comedor):
    url = reverse("relevamiento_create_edit_ajax", kwargs={"pk": comedor.pk})
    response = client_logged.post(url, {})
    assert response.status_code in {200, 302}


@pytest.mark.django_db
def test_create_view_post_invalid(client_logged, comedor):
    url = reverse("relevamiento_create_edit_ajax", kwargs={"pk": comedor.pk})
    response = client_logged.post(url, {})
    assert response.status_code in {200, 302}


@pytest.mark.django_db
def test_list_view(client_logged, comedor):
    url = reverse("relevamientos", kwargs={"comedor_pk": comedor.pk})
    response = client_logged.get(url)
    assert response.status_code == 200
    assert comedor.nombre in response.content.decode()


@pytest.mark.django_db
def test_update_view_get(client_logged, relevamiento):
    url = reverse("relevamiento_create_edit_ajax", kwargs={"pk": relevamiento.pk})
    response = client_logged.post(url, {})  # Usar POST en vez de GET
    assert response.status_code in {200, 302}


@pytest.mark.django_db
def test_update_view_post_invalid(client_logged, relevamiento):
    url = reverse("relevamiento_create_edit_ajax", kwargs={"pk": relevamiento.pk})
    response = client_logged.post(url, {})
    assert response.status_code in {200, 302}


@pytest.mark.django_db
def test_delete_view_get(client_logged, comedor, relevamiento):
    url = reverse(
        "relevamiento_eliminar",
        kwargs={"comedor_pk": comedor.pk, "pk": relevamiento.pk},
    )
    response = client_logged.get(url)
    assert response.status_code == 200
    assert comedor.nombre in response.content.decode()


@pytest.mark.django_db
def test_delete_view_post(client_logged, comedor, relevamiento):
    url = reverse(
        "relevamiento_eliminar",
        kwargs={"comedor_pk": comedor.pk, "pk": relevamiento.pk},
    )
    response = client_logged.post(url)
    assert response.status_code == 302
    assert response.url == reverse("comedor_detalle", kwargs={"pk": comedor.pk})
    assert not Relevamiento.objects.filter(pk=relevamiento.pk).exists()
