"""Tests for test pago expediente list."""

import pytest
from django.urls import reverse
from django.contrib.auth.models import User

from users.models import Profile
from core.models import Provincia
from celiaquia.models import PagoExpediente, PagoEstado


@pytest.mark.django_db
def test_pago_expediente_list_shows_pagos(client):
    provincia = Provincia.objects.create(nombre="Test")
    user = User.objects.create_user(username="user", password="pass")
    profile, _ = Profile.objects.get_or_create(user=user)
    profile.es_usuario_provincial = True
    profile.provincia = provincia
    profile.save()
    PagoExpediente.objects.create(
        provincia=provincia,
        periodo="2024-01",
        estado=PagoEstado.BORRADOR,
        creado_por=user,
    )
    client.force_login(user)
    url = reverse("pago_expediente_list", args=[provincia.id])
    response = client.get(url)
    assert response.status_code == 200
    assert "2024-01" in response.content.decode()
