"""Tests de normalización de datos opcionales en CiudadanoService."""

from datetime import date

import pytest

from celiaquia.services.ciudadano_service import CiudadanoService
from ciudadanos.models import Ciudadano
from core.models import Localidad, Municipio, Nacionalidad, Provincia, Sexo


@pytest.mark.django_db
def test_get_or_create_ciudadano_convierte_opcionales_vacios_en_none():
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    municipio = Municipio.objects.create(nombre="La Plata", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Centro", municipio=municipio)
    sexo = Sexo.objects.create(sexo="M")
    nacionalidad = Nacionalidad.objects.create(nacionalidad="Argentina")

    datos = {
        "tipo_documento": Ciudadano.DOCUMENTO_DNI,
        "documento": "12345678",
        "sexo": sexo.pk,
        "provincia": provincia.pk,
        "municipio": municipio.pk,
        "localidad": localidad.pk,
        "fecha_nacimiento": date(1990, 1, 1),
        "nombre": "Ana",
        "apellido": "Perez",
        "nacionalidad": nacionalidad.pk,
        "calle": "",
        "altura": "",
        "codigo_postal": "",
        "telefono": "",
        "email": "",
        "barrio": "",
        "piso_departamento": "",
    }

    ciudadano = CiudadanoService.get_or_create_ciudadano(datos)

    ciudadano.refresh_from_db()
    assert ciudadano.calle is None
    assert ciudadano.altura is None
    assert ciudadano.codigo_postal is None
    assert ciudadano.telefono is None
    assert ciudadano.email is None
    assert ciudadano.barrio is None
    assert ciudadano.piso_departamento is None

    Ciudadano.objects.filter(pk=ciudadano.pk).update(
        calle="",
        altura="",
        codigo_postal="",
        telefono="",
        email="",
        barrio="",
        piso_departamento="",
    )

    ciudadano = CiudadanoService.get_or_create_ciudadano(datos)
    ciudadano.refresh_from_db()
    assert ciudadano.calle is None
    assert ciudadano.altura is None
    assert ciudadano.codigo_postal is None
    assert ciudadano.telefono is None
    assert ciudadano.email is None
    assert ciudadano.barrio is None
    assert ciudadano.piso_departamento is None
