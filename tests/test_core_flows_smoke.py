"""Tests for test core flows smoke."""

import uuid

import pytest

pytestmark = [pytest.mark.smoke, pytest.mark.django_db]

API_BASE = "/api/centrodefamilia"


def _extract_results(response):
    data = response.json()
    if isinstance(data, list):
        return data
    return data.get("results", [])


def test_categoria_crud(api_client):
    list_url = f"{API_BASE}/categorias/"
    suffix = uuid.uuid4().hex[:8]

    create_payload = {"nombre": f"Smoke Categoria {suffix}"}
    response = api_client.post(list_url, create_payload, format="json")
    assert response.status_code in {200, 201}
    categoria_id = response.json()["id"]

    response = api_client.get(list_url)
    assert response.status_code == 200
    results = _extract_results(response)
    assert any(item["id"] == categoria_id for item in results)

    update_payload = {"nombre": f"Smoke Categoria Updated {suffix}"}
    response = api_client.patch(
        f"{list_url}{categoria_id}/",
        update_payload,
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["nombre"] == update_payload["nombre"]

    response = api_client.delete(f"{list_url}{categoria_id}/")
    assert response.status_code in {200, 204}


def test_actividad_crud(api_client):
    categoria_response = api_client.post(
        f"{API_BASE}/categorias/",
        {"nombre": f"Smoke Categoria {uuid.uuid4().hex[:8]}"},
        format="json",
    )
    assert categoria_response.status_code in {200, 201}
    categoria_id = categoria_response.json()["id"]

    list_url = f"{API_BASE}/actividades/"
    suffix = uuid.uuid4().hex[:8]
    create_payload = {"nombre": f"Smoke Actividad {suffix}", "categoria": categoria_id}
    response = api_client.post(list_url, create_payload, format="json")
    assert response.status_code in {200, 201}
    actividad_id = response.json()["id"]

    response = api_client.get(list_url)
    assert response.status_code == 200
    results = _extract_results(response)
    assert any(item["id"] == actividad_id for item in results)

    update_payload = {"nombre": f"Smoke Actividad Updated {suffix}"}
    response = api_client.patch(
        f"{list_url}{actividad_id}/",
        update_payload,
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["nombre"] == update_payload["nombre"]

    response = api_client.delete(f"{list_url}{actividad_id}/")
    assert response.status_code in {200, 204}
