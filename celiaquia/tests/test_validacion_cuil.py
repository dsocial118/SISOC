"""Validación de longitud del CUIL en los puntos de ingreso de Celiaquía."""

from datetime import date
from io import BytesIO
import json

import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from openpyxl import Workbook

from celiaquia.models import (
    EstadoExpediente,
    EstadoLegajo,
    Expediente,
    ExpedienteCiudadano,
    RegistroErroneo,
)
from celiaquia.services.importacion_service import (
    ImportacionService,
    validar_cuil_importacion,
)
from ciudadanos.models import Ciudadano
from core.models import Localidad, Municipio, Nacionalidad, Provincia, Sexo
from users.models import Profile

CUIL_VALIDO = "20123456783"
CUIL_CORTO = "2012345678"
CUIL_LARGO = "201234567830"

HEADERS_EXCEL = [
    "apellido",
    "nombre",
    "documento",
    "fecha_nacimiento",
    "sexo",
    "nacionalidad",
    "municipio",
    "localidad",
    "calle",
    "altura",
    "codigo_postal",
    "telefono",
    "email",
    "APELLIDO_RESPONSABLE",
    "NOMBRE_REPSONSABLE",
    "Cuit_Responsable",
    "FECHA_DE_NACIMIENTO_RESPONSABLE",
    "SEXO_RESPONSABLE",
    "DOMICILIO_RESPONSABLE",
    "LOCALIDAD_RESPONSABLE",
    "CELULAR_RESPONSABLE",
    "CORREO_RESPONSABLE",
]


def _crear_usuario_provincial(username="prov_cuil"):
    provincia = Provincia.objects.create(nombre=f"Provincia {username}")
    user = User.objects.create_user(username=username, password="pass")
    profile, _ = Profile.objects.get_or_create(user=user)
    profile.es_usuario_provincial = True
    profile.provincia = provincia
    profile.save()
    return user, provincia


def _crear_archivo_excel(row):
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(HEADERS_EXCEL)
    worksheet.append(row)
    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return SimpleUploadedFile(
        "expediente.xlsx",
        buffer.getvalue(),
        content_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    )


def _fila_excel(documento, municipio, localidad):
    return [
        "Perez",
        "Ana",
        documento,
        "01/01/1980",
        "F",
        "Argentina",
        municipio.pk,
        localidad.pk,
        "Calle 1",
        "123",
        "1000",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
    ]


def _contexto_importacion(username, superuser=False):
    user, provincia = _crear_usuario_provincial(username)
    if superuser:
        user.is_superuser = True
        user.save(update_fields=["is_superuser"])
    expediente = Expediente.objects.create(
        usuario_provincia=user,
        estado=EstadoExpediente.objects.create(nombre="CREADO"),
    )
    EstadoLegajo.objects.create(nombre="DOCUMENTO_PENDIENTE")
    Sexo.objects.create(sexo="Masculino")
    Sexo.objects.create(sexo="Femenino")
    Nacionalidad.objects.create(nacionalidad="Argentina")
    municipio = Municipio.objects.create(nombre="La Plata", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Centro", municipio=municipio)
    return user, expediente, municipio, localidad


@pytest.mark.parametrize("valor", [CUIL_CORTO, CUIL_LARGO, "123", ""])
def test_validar_cuil_rechaza_longitudes_distintas_de_once(valor):
    with pytest.raises(ValidationError):
        validar_cuil_importacion(valor)


def test_validar_cuil_acepta_once_digitos():
    assert validar_cuil_importacion(CUIL_VALIDO) == CUIL_VALIDO


def test_validar_cuil_informa_la_longitud_esperada():
    with pytest.raises(ValidationError) as exc:
        validar_cuil_importacion(CUIL_CORTO)
    assert "11" in " ".join(exc.value.messages)


@pytest.mark.django_db
def test_importacion_rechaza_cuil_de_diez_digitos():
    user, expediente, municipio, localidad = _contexto_importacion("prov_cuil_corto")

    resultado = ImportacionService.importar_legajos_desde_excel(
        expediente=expediente,
        archivo_excel=_crear_archivo_excel(
            _fila_excel(CUIL_CORTO, municipio, localidad)
        ),
        usuario=user,
    )

    assert resultado["validos"] == 0
    assert resultado["errores"] == 1
    assert ExpedienteCiudadano.objects.count() == 0

    registro = RegistroErroneo.objects.get(expediente=expediente)
    assert "11" in registro.mensaje_error


@pytest.mark.django_db
def test_importacion_acepta_cuil_de_once_digitos():
    user, expediente, municipio, localidad = _contexto_importacion("prov_cuil_ok")

    resultado = ImportacionService.importar_legajos_desde_excel(
        expediente=expediente,
        archivo_excel=_crear_archivo_excel(
            _fila_excel(CUIL_VALIDO, municipio, localidad)
        ),
        usuario=user,
    )

    assert resultado["errores"] == 0
    assert resultado["validos"] == 1
    assert ExpedienteCiudadano.objects.count() == 1


@pytest.mark.django_db
def test_actualizar_registro_erroneo_rechaza_cuil_de_diez_digitos(client):
    user, expediente, municipio, localidad = _contexto_importacion(
        "prov_cuil_reg", superuser=True
    )

    ImportacionService.importar_legajos_desde_excel(
        expediente=expediente,
        archivo_excel=_crear_archivo_excel(
            _fila_excel(CUIL_CORTO, municipio, localidad)
        ),
        usuario=user,
    )
    registro = RegistroErroneo.objects.get(expediente=expediente)

    client.force_login(user)
    response = client.post(
        reverse("registro_erroneo_actualizar", args=[expediente.pk, registro.pk]),
        data=json.dumps({"documento": CUIL_CORTO}),
        content_type="application/json",
    )

    assert response.status_code == 400
    assert "11" in json.loads(response.content)["error"]


@pytest.mark.django_db
def test_legajo_editar_rechaza_cuil_de_diez_digitos(client):
    user, expediente, municipio, localidad = _contexto_importacion(
        "prov_cuil_edit", superuser=True
    )
    sexo = Sexo.objects.get(sexo="Femenino")
    nacionalidad = Nacionalidad.objects.get(nacionalidad="Argentina")

    ciudadano = Ciudadano.objects.create(
        apellido="Perez",
        nombre="Ana",
        fecha_nacimiento=date(1980, 1, 1),
        documento=CUIL_VALIDO,
        sexo=sexo,
        nacionalidad=nacionalidad,
        municipio=municipio,
        localidad=localidad,
    )
    legajo = ExpedienteCiudadano.objects.create(
        expediente=expediente,
        ciudadano=ciudadano,
        estado=EstadoLegajo.objects.get(nombre="DOCUMENTO_PENDIENTE"),
    )

    client.force_login(user)
    response = client.post(
        reverse("legajo_editar", args=[expediente.pk, legajo.pk]),
        data={
            "apellido": "Perez",
            "nombre": "Ana",
            "documento": CUIL_CORTO,
            "fecha_nacimiento": "1980-01-01",
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

    assert response.status_code == 400
    assert "11" in json.loads(response.content)["error"]

    ciudadano.refresh_from_db()
    assert str(ciudadano.documento) == CUIL_VALIDO
