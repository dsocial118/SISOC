"""Tests for test importacion codigo postal telefono."""

from io import BytesIO
from datetime import date

import pandas as pd
import pytest
from django.contrib.auth import get_user_model

from celiaquia.models import EstadoExpediente, EstadoLegajo, Expediente
from celiaquia.services.importacion_service import ImportacionService
from ciudadanos.models import Ciudadano
from core.models import Localidad, Municipio, Nacionalidad, Provincia, Sexo
from users.models import Profile


def _crear_usuario_provincial(username="tester"):
    provincia = Provincia.objects.create(nombre=f"Provincia {username}")
    user = get_user_model().objects.create_user(username=username, password="pass")
    profile, _ = Profile.objects.get_or_create(user=user)
    profile.es_usuario_provincial = True
    profile.provincia = provincia
    profile.save()
    return get_user_model().objects.get(pk=user.pk), provincia


@pytest.mark.django_db
def test_import_with_postal_code_and_phone():
    user, provincia = _crear_usuario_provincial()
    estado_exp = EstadoExpediente.objects.create(nombre="CREADO")
    expediente = Expediente.objects.create(usuario_provincia=user, estado=estado_exp)
    EstadoLegajo.objects.create(nombre="DOCUMENTO_PENDIENTE")
    Sexo.objects.create(sexo="Masculino")
    Sexo.objects.create(sexo="Femenino")
    Nacionalidad.objects.create(nacionalidad="Argentina")
    municipio = Municipio.objects.create(nombre="La Plata", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Centro", municipio=municipio)
    df = pd.DataFrame(
        [
            {
                "apellido": "Perez",
                "nombre": "Juan",
                "documento": 1234567890,
                "fecha_nacimiento": date(1990, 1, 1),
                "sexo": "M",
                "nacionalidad": "Argentina",
                "municipio": municipio.pk,
                "localidad": localidad.pk,
                "calle": "Calle 1",
                "altura": 123,
                "telefono": 3815237945,
                "codigo_postal": 1406,
                "apellido_responsable": "Gomez",
                "nombre_responsable": "Laura",
                "documento_responsable": 20123456789,
                "fecha_nacimiento_responsable": date(1980, 1, 1),
                "sexo_responsable": "F",
                "domicilio_responsable": "Calle Resp 123",
                "localidad_responsable": localidad.nombre,
            }
        ]
    )
    bio = BytesIO()
    df.to_excel(bio, index=False)
    bio.seek(0)

    ImportacionService.importar_legajos_desde_excel(expediente, bio, user)

    ciudadano = Ciudadano.objects.get(documento=1234567890)
    assert str(ciudadano.telefono) == "3815237945"
    assert str(ciudadano.codigo_postal) == "1406"
