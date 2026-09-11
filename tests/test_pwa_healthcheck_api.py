"""Contrato del health-check que la PWA consulta antes de enviar documentación."""

import pytest
from django.db import DatabaseError
from django.db.utils import InterfaceError
from django.test import Client
from django.urls import reverse


@pytest.fixture(name="client")
def fixture_client():
    return Client()


@pytest.mark.django_db
def test_healthcheck_pwa_responde_ok_sin_autenticacion(client):
    response = client.get(reverse("pwa-health-list"))

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


@pytest.mark.django_db
def test_healthcheck_pwa_devuelve_503_si_la_base_no_responde(client, mocker):
    mocker.patch(
        "pwa.api_views.connection.cursor",
        side_effect=DatabaseError("conexión caída"),
    )

    response = client.get(reverse("pwa-health-list"))

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "database": "unavailable"}


@pytest.mark.django_db
def test_healthcheck_pwa_trata_la_conexion_rota_como_indisponible(client, mocker):
    """`InterfaceError` no hereda de `DatabaseError`: es la conexión caída."""
    mocker.patch(
        "pwa.api_views.connection.cursor",
        side_effect=InterfaceError("connection already closed"),
    )

    response = client.get(reverse("pwa-health-list"))

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "database": "unavailable"}


@pytest.mark.django_db
def test_healthcheck_pwa_no_expone_detalle_interno_del_error(client, mocker):
    mocker.patch(
        "pwa.api_views.connection.cursor",
        side_effect=DatabaseError("Access denied for user 'sisoc'@'10.0.0.5'"),
    )

    response = client.get(reverse("pwa-health-list"))

    cuerpo = response.content.decode()
    assert "Access denied" not in cuerpo
    assert "10.0.0.5" not in cuerpo


@pytest.mark.django_db
def test_healthcheck_pwa_se_recupera_cuando_la_base_vuelve(client, mocker):
    mocker.patch(
        "pwa.api_views.connection.cursor",
        side_effect=DatabaseError("caída transitoria"),
    )
    assert client.get(reverse("pwa-health-list")).status_code == 503

    mocker.stopall()

    assert client.get(reverse("pwa-health-list")).status_code == 200


@pytest.mark.django_db
def test_healthcheck_infra_sigue_siendo_texto_plano(client):
    """`/health/` es la sonda de infraestructura y no cambia de contrato."""
    response = client.get(reverse("health_check"))

    assert response.status_code == 200
    assert response.content == b"OK"
