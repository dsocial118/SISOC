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


@pytest.mark.django_db
def test_legajo_editar_get_devuelve_nacionalidad_actual_y_municipio_desde_localidad(client):
    user = User.objects.create_superuser(
        username="tecnico_get",
        email="tecnico_get@example.com",
        password="pass",
    )

    provincia = Provincia.objects.create(nombre="Buenos Aires")
    municipio = Municipio.objects.create(nombre="La Plata", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Centro", municipio=municipio)
    sexo = Sexo.objects.create(sexo="M")
    argentina = Nacionalidad.objects.create(nacionalidad="Argentina")
    uruguaya = Nacionalidad.objects.create(nacionalidad="Uruguaya")
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
        nacionalidad=uruguaya,
        localidad=localidad,
    )
    legajo = ExpedienteCiudadano.objects.create(
        expediente=expediente,
        ciudadano=ciudadano,
        estado=estado_legajo,
    )

    client.force_login(user)
    response = client.get(reverse("legajo_editar", args=[expediente.pk, legajo.pk]))

    assert response.status_code == 200
    payload = response.json()["legajo"]
    assert payload["nacionalidad"] == uruguaya.pk
    assert payload["municipio"] == municipio.pk
    assert payload["localidad"] == localidad.pk


@pytest.mark.django_db
def test_legajo_editar_actualiza_nacionalidad_elegida_y_municipio_desde_localidad(client):
    user = User.objects.create_superuser(
        username="tecnico_defaults",
        email="tecnico_defaults@example.com",
        password="pass",
    )

    provincia = Provincia.objects.create(nombre="Buenos Aires")
    municipio_origen = Municipio.objects.create(nombre="La Plata", provincia=provincia)
    localidad_origen = Localidad.objects.create(
        nombre="Centro", municipio=municipio_origen
    )
    municipio_destino = Municipio.objects.create(nombre="Berisso", provincia=provincia)
    localidad_destino = Localidad.objects.create(
        nombre="Villa Nueva", municipio=municipio_destino
    )
    sexo = Sexo.objects.create(sexo="M")
    argentina = Nacionalidad.objects.create(nacionalidad="Argentina")
    uruguaya = Nacionalidad.objects.create(nacionalidad="Uruguaya")
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
        nacionalidad=uruguaya,
        municipio=municipio_origen,
        localidad=localidad_origen,
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
            "nacionalidad": uruguaya.pk,
            "telefono": "",
            "email": "",
            "calle": "",
            "altura": "",
            "codigo_postal": "",
            "municipio": municipio_origen.pk,
            "localidad": localidad_destino.pk,
        },
    )

    assert response.status_code == 200
    ciudadano.refresh_from_db()
    assert ciudadano.nacionalidad_id == uruguaya.pk
    assert ciudadano.municipio_id == municipio_destino.pk
    assert ciudadano.localidad_id == localidad_destino.pk


@pytest.mark.django_db
def test_legajo_editar_rechaza_nacionalidad_faltante(client):
    user = User.objects.create_superuser(
        username="tecnico_no_nacionalidad",
        email="tecnico_no_nacionalidad@example.com",
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
            "nacionalidad": "",
            "telefono": "",
            "email": "",
            "calle": "",
            "altura": "",
            "codigo_postal": "",
            "municipio": municipio.pk,
            "localidad": localidad.pk,
        },
    )

    assert response.status_code == 400
    ciudadano.refresh_from_db()
    assert ciudadano.nacionalidad_id == nacionalidad.pk
