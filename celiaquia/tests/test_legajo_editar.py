"""Tests de regresión para la edición de legajos en Celiaquía."""

from datetime import date

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from celiaquia.models import (
    EstadoExpediente,
    EstadoLegajo,
    Expediente,
    ExpedienteCiudadano,
)
from ciudadanos.models import Ciudadano
from core.models import Localidad, Municipio, Nacionalidad, Provincia, Sexo


@pytest.mark.django_db
def test_legajo_editar_convierte_altura_y_telefono_vacios_en_none(client):
    user = User.objects.create_superuser(
        username="tecnico",
        email="tecnico@example.com",
        password="pass",
    )

    provincia = Provincia.objects.create(nombre="Buenos Aires")
    municipio = Municipio.objects.create(nombre="La Plata", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Centro", municipio=municipio)
    sexo = Sexo.objects.create(sexo="M")
    nacionalidad = Nacionalidad.objects.create(nacionalidad="Argentina")
    estado_expediente = EstadoExpediente.objects.create(nombre="CREADO")
    estado_legajo = EstadoLegajo.objects.create(nombre="DOCUMENTO_PENDIENTE")

    expediente = Expediente.objects.create(
        usuario_provincia=user,
        estado=estado_expediente,
    )
    ciudadano = Ciudadano.objects.create(
        apellido="Perez",
        nombre="Ana",
        fecha_nacimiento=date(1990, 1, 1),
        documento=12345678,
        sexo=sexo,
        nacionalidad=nacionalidad,
        municipio=municipio,
        localidad=localidad,
        altura="180",
        telefono="123456789",
    )
    legajo = ExpedienteCiudadano.objects.create(
        expediente=expediente,
        ciudadano=ciudadano,
        estado=estado_legajo,
    )

    client.force_login(user)
    response = client.post(
        reverse("legajo_editar", args=[expediente.pk, legajo.pk]),
        data={
            "apellido": "Perez",
            "nombre": "Ana",
            "documento": "12345678",
            "fecha_nacimiento": "1990-01-01",
            "sexo": sexo.pk,
            "nacionalidad": nacionalidad.pk,
            "telefono": "",
            "email": "",
            "calle": "",
            "altura": "",
            "codigo_postal": "",
            "municipio": municipio.pk,
            "localidad": localidad.pk,
        },
    )

    assert response.status_code == 200
    ciudadano.refresh_from_db()
    assert ciudadano.email is None
    assert ciudadano.calle is None
    assert ciudadano.altura is None
    assert ciudadano.codigo_postal is None
    assert ciudadano.telefono is None
