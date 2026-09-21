"""Smoke del acceso autenticado al mapa de arquitectura."""

import pytest
from django.contrib.auth.views import redirect_to_login
from django.urls import reverse

pytestmark = [pytest.mark.django_db, pytest.mark.smoke]


def test_mapa_arquitectura_requires_login(client, settings):
    url = reverse("mapa_arquitectura")
    assert url == "/arquitectura/"

    response = client.get(url)

    assert response.status_code == 302
    assert response.url == redirect_to_login(url, settings.LOGIN_URL).url


def test_mapa_arquitectura_authenticated(client, user):
    client.force_login(user)

    response = client.get(reverse("mapa_arquitectura"))

    assert response.status_code == 200
    assert "core/mapa_arquitectura.html" in [t.name for t in response.templates]
    assert isinstance(response.context["grafo_disponible"], bool)
    assert response.context["generado"] is None or isinstance(
        response.context["generado"], str
    )
