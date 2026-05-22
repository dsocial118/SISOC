"""Tests para la exportacion del padron final de aprobados (issue #1724)."""

import datetime
from io import BytesIO

import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from openpyxl import load_workbook

from celiaquia.models import (
    EstadoExpediente,
    EstadoLegajo,
    Expediente,
    ExpedienteCiudadano,
    ResultadoSintys,
    RevisionTecnico,
)
from ciudadanos.models import Ciudadano, GrupoFamiliar
from core.models import Localidad, Municipio, Provincia, Sexo


COLUMNAS_ESPERADAS = [
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


@pytest.mark.django_db
def test_padron_final_export_estructura_y_formato(client):
    admin = User.objects.create_superuser(username="admin", password="pass")

    provincia = Provincia.objects.create(nombre="Buenos Aires")
    municipio = Municipio.objects.create(nombre="La Plata", provincia=provincia)
    localidad = Localidad.objects.create(nombre="City Bell", municipio=municipio)
    municipio_resp = Municipio.objects.create(nombre="Quilmes", provincia=provincia)
    localidad_resp = Localidad.objects.create(
        nombre="Bernal", municipio=municipio_resp
    )
    sexo_f = Sexo.objects.create(sexo="Femenino")
    sexo_m = Sexo.objects.create(sexo="Masculino")

    estado_exp = EstadoExpediente.objects.create(nombre="ASIGNADO")
    estado_leg = EstadoLegajo.objects.create(nombre="VALIDO")
    expediente = Expediente.objects.create(
        usuario_provincia=admin, estado=estado_exp
    )

    beneficiario = Ciudadano.objects.create(
        apellido="Perez",
        nombre="Juan",
        fecha_nacimiento=datetime.date(2015, 6, 10),
        documento=12345678,
        tipo_documento=Ciudadano.DOCUMENTO_DNI,
        sexo=sexo_m,
        provincia=provincia,
        municipio=municipio,
        localidad=localidad,
        calle="Calle Falsa",
        altura="123",
        codigo_postal="1900",
        telefono="2211234567",
        email="juan@example.com",
    )
    responsable = Ciudadano.objects.create(
        apellido="Perez",
        nombre="Maria",
        fecha_nacimiento=datetime.date(1985, 3, 22),
        documento=23456789,
        cuil_cuit="27234567893",
        tipo_documento=Ciudadano.DOCUMENTO_DNI,
        sexo=sexo_f,
        provincia=provincia,
        municipio=municipio_resp,
        localidad=localidad_resp,
        calle="Av. Siempre Viva",
        altura="742",
        telefono="2219876543",
        email="maria@example.com",
    )
    GrupoFamiliar.objects.create(
        ciudadano_1=responsable,
        ciudadano_2=beneficiario,
        vinculo=GrupoFamiliar.RELACION_PADRE,
        cuidador_principal=True,
    )

    no_aprobado = Ciudadano.objects.create(
        apellido="Lopez",
        nombre="Pedro",
        fecha_nacimiento=datetime.date(2010, 1, 1),
        documento=34567890,
        tipo_documento=Ciudadano.DOCUMENTO_DNI,
    )

    ExpedienteCiudadano.objects.create(
        expediente=expediente,
        ciudadano=beneficiario,
        estado=estado_leg,
        rol=ExpedienteCiudadano.ROLE_BENEFICIARIO,
        revision_tecnico=RevisionTecnico.APROBADO,
        resultado_sintys=ResultadoSintys.MATCH,
    )
    ExpedienteCiudadano.objects.create(
        expediente=expediente,
        ciudadano=responsable,
        estado=estado_leg,
        rol=ExpedienteCiudadano.ROLE_RESPONSABLE,
        revision_tecnico=RevisionTecnico.APROBADO,
        resultado_sintys=ResultadoSintys.MATCH,
    )
    ExpedienteCiudadano.objects.create(
        expediente=expediente,
        ciudadano=no_aprobado,
        estado=estado_leg,
        rol=ExpedienteCiudadano.ROLE_BENEFICIARIO,
        revision_tecnico=RevisionTecnico.PENDIENTE,
        resultado_sintys=ResultadoSintys.SIN_CRUCE,
    )

    client.force_login(admin)
    response = client.get(
        reverse("expediente_padron_final_export", args=[expediente.pk])
    )
    assert response.status_code == 200

    wb = load_workbook(BytesIO(response.content))
    ws = wb.active

    header = [cell.value for cell in next(ws.iter_rows(max_row=1))]
    assert header == COLUMNAS_ESPERADAS

    filas = list(ws.iter_rows(min_row=2, values_only=True))
    assert len(filas) == 1, "Solo el beneficiario aprobado debe figurar"

    fila = dict(zip(COLUMNAS_ESPERADAS, filas[0]))

    assert fila["apellido"] == "Perez"
    assert fila["nombre"] == "Juan"
    assert str(fila["documento"]) == "12345678"

    assert fila["fecha_nacimiento"] == "10/06/2015"
    assert ":" not in str(fila["fecha_nacimiento"])

    assert fila["municipio"] == "La Plata"
    assert fila["localidad"] == "City Bell"
    assert str(fila["municipio"]) != str(municipio.pk)
    assert str(fila["localidad"]) != str(localidad.pk)

    assert fila["sexo"] == "Masculino"
    assert fila["calle"] == "Calle Falsa"
    assert fila["altura"] == "123"
    assert fila["telefono"] == "2211234567"
    assert fila["email"] == "juan@example.com"

    assert fila["APELLIDO_RESPONSABLE"] == "Perez"
    assert fila["NOMBRE_REPSONSABLE"] == "Maria"
    assert fila["Cuit_Responsable"] == "27234567893"
    assert fila["FECHA_DE_NACIMIENTO_RESPONSABLE"] == "22/03/1985"
    assert fila["SEXO_RESPONSABLE"] == "Femenino"
    assert fila["DOMICILIO_RESPONSABLE"] == "Av. Siempre Viva 742"
    assert fila["LOCALIDAD_RESPONSABLE"] == "Bernal"
    assert str(fila["LOCALIDAD_RESPONSABLE"]) != str(localidad_resp.pk)
    assert fila["CELULAR_RESPONSABLE"] == "2219876543"
    assert fila["CORREO_RESPONSABLE"] == "maria@example.com"
