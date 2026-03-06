from django.test import Client


def test_pwa_health_endpoint_returns_ok():
    client = Client()
    response = client.get("/api/pwa/health/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
