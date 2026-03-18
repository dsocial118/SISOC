"""Tests de regresión para detalle de expedientes en Celiaquía."""

from datetime import date

import pytest
from django.contrib.auth.models import Permission, User
from django.urls import reverse

from celiaquia.models import (
    EstadoExpediente,
    EstadoLegajo,
    Expediente,
    ExpedienteCiudadano,
)
from ciudadanos.models import Ciudadano


@pytest.mark.django_db
def test_expediente_detail_no_duplica_legajos_sin_responsable(client):
    user = User.objects.create_user(username="prov", password="pass")
    permission = Permission.objects.get(
        content_type__app_label="celiaquia",
        codename="view_expediente",
    )
    user.user_permissions.add(permission)

    estado_expediente = EstadoExpediente.objects.create(nombre="CREADO")
    expediente = Expediente.objects.create(
        usuario_provincia=user,
        estado=estado_expediente,
    )
    estado_legajo = EstadoLegajo.objects.create(nombre="DOCUMENTO_PENDIENTE")
    ciudadano = Ciudadano.objects.create(
        apellido="Perez",
        nombre="Ana",
        fecha_nacimiento=date(2010, 1, 1),
        documento=12345678,
    )
    legajo = ExpedienteCiudadano.objects.create(
        expediente=expediente,
        ciudadano=ciudadano,
        estado=estado_legajo,
    )

    client.force_login(user)
    response = client.get(reverse("expediente_detail", args=[expediente.pk]))

    assert response.status_code == 200
    legajos_ids = [item.pk for item in response.context["legajos_enriquecidos"]]
    assert legajos_ids.count(legajo.pk) == 1
    assert len(legajos_ids) == 1
