import pytest
from django.urls import reverse
from ciudadanos.models import Ciudadano


@pytest.mark.django_db
def test_buscar_ciudadano_html(client):
    ciudadano = Ciudadano.objects.create(
        apellido="Perez",
        nombre="Juan",
        fecha_nacimiento="1990-01-01",
        documento=12345678,
    )
    url = reverse("buscar_ciudadano")
    response = client.get(url, {"query": str(ciudadano.documento)})
    assert response.status_code == 200
    data = response.json()
    assert "html" in data
    assert "Perez" in data["html"]
