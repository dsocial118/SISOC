"""Regresiones de render para el listado de expedientes de Celiaquía."""

import pytest
from django.contrib.auth.models import Permission, User
from django.urls import reverse

from celiaquia.models import EstadoExpediente, Expediente
from core.models import Provincia
from users.models import Profile


@pytest.mark.django_db
def test_expediente_list_renderiza_sin_filtros_legacy(client):
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    user = User.objects.create_user(username="prov", password="pass")
    permission = Permission.objects.get(
        content_type__app_label="celiaquia",
        codename="view_expediente",
    )
    user.user_permissions.add(permission)

    profile, _ = Profile.objects.get_or_create(user=user)
    profile.es_usuario_provincial = True
    profile.provincia = provincia
    profile.save()

    estado = EstadoExpediente.objects.create(nombre="CREADO")
    expediente = Expediente.objects.create(usuario_provincia=user, estado=estado)

    client.force_login(user)
    response = client.get(reverse("expediente_list"))

    assert response.status_code == 200
    content = response.content.decode()
    assert str(expediente.pk) in content
    assert provincia.nombre in content
    assert "Invalid filter" not in content
