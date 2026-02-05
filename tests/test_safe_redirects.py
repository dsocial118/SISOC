import pytest
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone

from ciudadanos.models import Ciudadano, GrupoFamiliar
from core.security import safe_redirect


@pytest.mark.django_db
def test_safe_redirect_blocks_external_next():
    rf = RequestFactory()
    request = rf.get("/dummy", {"next": "https://evil.com"})
    response = safe_redirect(request, default="/safe")
    assert response.status_code == 302
    assert response["Location"] == "/safe"


@pytest.mark.django_db
def test_safe_redirect_allows_internal_next():
    rf = RequestFactory()
    request = rf.get("/dummy", {"next": "/ruta/interna"})
    response = safe_redirect(request, default="/safe")
    assert response.status_code == 302
    assert response["Location"] == "/ruta/interna"


def _crear_ciudadano(**kwargs):
    data = {
        "apellido": "Perez",
        "nombre": "Juan",
        "fecha_nacimiento": timezone.now().date(),
        "documento": 12345678,
    }
    data.update(kwargs)
    return Ciudadano.objects.create(**data)


@pytest.mark.django_db
def test_grupo_familiar_delete_blocks_external_next(auth_client):
    ciudadano_1 = _crear_ciudadano(documento=11111111)
    ciudadano_2 = _crear_ciudadano(documento=22222222, nombre="Maria")
    relacion = GrupoFamiliar.objects.create(
        ciudadano_1=ciudadano_1,
        ciudadano_2=ciudadano_2,
    )

    url = reverse("grupofamiliar_eliminar", kwargs={"pk": relacion.pk})
    response = auth_client.post(url, {"next": "https://evil.com"})

    assert response.status_code == 302
    assert response["Location"] == ciudadano_1.get_absolute_url()


@pytest.mark.django_db
def test_grupo_familiar_delete_allows_internal_next(auth_client):
    ciudadano_1 = _crear_ciudadano(documento=33333333)
    ciudadano_2 = _crear_ciudadano(documento=44444444, nombre="Ana")
    relacion = GrupoFamiliar.objects.create(
        ciudadano_1=ciudadano_1,
        ciudadano_2=ciudadano_2,
    )

    url = reverse("grupofamiliar_eliminar", kwargs={"pk": relacion.pk})
    response = auth_client.post(url, {"next": "/ciudadanos/listar"})

    assert response.status_code == 302
    assert response["Location"] == "/ciudadanos/listar"
