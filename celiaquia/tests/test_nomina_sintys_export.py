"""Tests for test nomina sintys export."""

from io import BytesIO

import pytest
from django.contrib.auth.models import Group, User
from django.urls import reverse
from openpyxl import load_workbook

from celiaquia.models import (
    Expediente,
    EstadoExpediente,
    EstadoLegajo,
    ExpedienteCiudadano,
)
from ciudadanos.models import Ciudadano


@pytest.mark.django_db
def test_exportar_nomina_sintys(client):
    grupo = Group.objects.create(name="TecnicoCeliaquia")
    user = User.objects.create_user(username="tec", password="pass")
    user.groups.add(grupo)

    estado_exp = EstadoExpediente.objects.create(nombre="ASIGNADO")
    estado_leg = EstadoLegajo.objects.create(nombre="VALIDO")
    creador = User.objects.create_user(username="prov", password="pass")
    expediente = Expediente.objects.create(usuario_provincia=creador, estado=estado_exp)

    ciudadano = Ciudadano.objects.create(
        apellido="Perez",
        nombre="Juan",
        fecha_nacimiento="2000-01-01",
        documento=12345678,
        tipo_documento=Ciudadano.DOCUMENTO_DNI,
    )
    ExpedienteCiudadano.objects.create(
        expediente=expediente, ciudadano=ciudadano, estado=estado_leg
    )

    client.force_login(user)
    url = reverse("expediente_nomina_sintys_export", args=[expediente.pk])
    response = client.get(url)
    assert response.status_code == 200

    wb = load_workbook(BytesIO(response.content))
    ws = wb.active
    header = [cell.value for cell in next(ws.iter_rows(max_row=1))]
    assert header == ["Numero_documento", "TipoDocumento", "nombre", "apellido"]
    row = [cell.value for cell in next(ws.iter_rows(min_row=2, max_row=2))]
    assert str(row[0]) == "12345678"
    assert row[1] == "DNI"
