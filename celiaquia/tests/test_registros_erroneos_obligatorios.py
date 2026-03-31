"""Regresiones para campos obligatorios en registros erróneos de Celiaquía."""

from datetime import date
from io import BytesIO
import json
import re

import pytest
from django.contrib.auth.models import Permission, User
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
from celiaquia.services.importacion_service import ImportacionService
from core.models import Localidad, Municipio, Nacionalidad, Provincia, Sexo
from users.models import Profile


def _crear_usuario_provincial(username="prov"):
    provincia = Provincia.objects.create(nombre=f"Provincia {username}")
    user = User.objects.create_user(username=username, password="pass")
    profile, _ = Profile.objects.get_or_create(user=user)
    profile.es_usuario_provincial = True
    profile.provincia = provincia
    profile.save()
    return user, provincia


def _crear_contexto_expediente(user):
    estado_expediente = EstadoExpediente.objects.create(nombre="CREADO")
    return Expediente.objects.create(usuario_provincia=user, estado=estado_expediente)


def _crear_archivo_excel(headers, row):
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(headers)
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


def _fecha_hace_anos(anos):
    hoy = date.today()
    try:
        fecha = hoy.replace(year=hoy.year - anos)
    except ValueError:
        fecha = hoy.replace(month=2, day=28, year=hoy.year - anos)
    return fecha.strftime("%d/%m/%Y")


@pytest.mark.django_db
def test_importacion_con_sexo_faltante_genera_registro_erroneo():
    user, provincia = _crear_usuario_provincial("prov_import")
    expediente = _crear_contexto_expediente(user)
    EstadoLegajo.objects.create(nombre="DOCUMENTO_PENDIENTE")
    Sexo.objects.create(sexo="Masculino")
    Sexo.objects.create(sexo="Femenino")
    Nacionalidad.objects.create(nacionalidad="Argentina")
    municipio = Municipio.objects.create(nombre="La Plata", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Centro", municipio=municipio)

    archivo = _crear_archivo_excel(
        headers=[
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
        ],
        row=[
            "Perez",
            "Ana",
            "30123456789",
            "01/01/2010",
            "",
            "Argentina",
            municipio.pk,
            localidad.pk,
            "Calle 1",
            "123",
            "1000",
            "",
            "",
            "Gomez",
            "Laura",
            "20123456789",
            "01/01/1980",
            "F",
            "Calle Resp 123",
            localidad.nombre,
            "",
            "",
        ],
    )

    resultado = ImportacionService.importar_legajos_desde_excel(
        expediente=expediente,
        archivo_excel=archivo,
        usuario=user,
    )

    assert resultado["validos"] == 0
    assert resultado["errores"] == 1
    assert ExpedienteCiudadano.objects.count() == 0

    registro = RegistroErroneo.objects.get(expediente=expediente)
    assert "sexo" in registro.mensaje_error.lower()


@pytest.mark.django_db
def test_detalle_expediente_muestra_campos_responsable_para_registros_erroneos(client):
    user, provincia = _crear_usuario_provincial("prov_detail")
    permission = Permission.objects.get(
        content_type__app_label="celiaquia",
        codename="view_expediente",
    )
    user.user_permissions.add(permission)

    expediente = _crear_contexto_expediente(user)
    municipio = Municipio.objects.create(nombre="La Plata", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Centro", municipio=municipio)
    Nacionalidad.objects.create(nacionalidad="Argentina")
    Sexo.objects.create(sexo="Masculino")
    Sexo.objects.create(sexo="Femenino")
    RegistroErroneo.objects.create(
        expediente=expediente,
        fila_excel=2,
        datos_raw={
            "apellido": "Perez",
            "nombre": "Ana",
            "documento": "12345678",
            "fecha_nacimiento": "01/01/2010",
            "sexo": "Masculino",
            "nacionalidad": "Argentina",
            "municipio": str(municipio.pk),
            "localidad": str(localidad.pk),
            "calle": "Calle 1",
            "altura": "123",
            "codigo_postal": "1000",
        },
        mensaje_error="Faltan campos obligatorios: apellido_responsable",
    )

    client.force_login(user)
    response = client.get(reverse("expediente_detail", args=[expediente.pk]))

    assert response.status_code == 200
    content = response.content.decode()
    assert 'name="apellido_responsable"' in content
    assert 'name="localidad_responsable"' in content
    assert "Apellido Responsable *" in content


@pytest.mark.django_db
def test_detalle_expediente_autocompleta_sexo_m_f_en_registros_erroneos(client):
    user, provincia = _crear_usuario_provincial("prov_detail_sexo_mf")
    permission = Permission.objects.get(
        content_type__app_label="celiaquia",
        codename="view_expediente",
    )
    user.user_permissions.add(permission)

    expediente = _crear_contexto_expediente(user)
    municipio = Municipio.objects.create(nombre="La Plata", provincia=provincia)
    Nacionalidad.objects.create(nacionalidad="Argentina")
    sexo_m = Sexo.objects.create(sexo="Masculino")
    sexo_f = Sexo.objects.create(sexo="Femenino")
    RegistroErroneo.objects.create(
        expediente=expediente,
        fila_excel=3,
        datos_raw={
            "apellido": "Perez",
            "nombre": "Ana",
            "documento": "12345678",
            "fecha_nacimiento": "01/01/2010",
            "sexo": "M",
            "nacionalidad": "Argentina",
            "municipio": str(municipio.pk),
            "localidad": "999999",
            "calle": "Calle 1",
            "altura": "123",
            "codigo_postal": "1000",
            "apellido_responsable": "Gomez",
            "nombre_responsable": "Laura",
            "documento_responsable": "20123456789",
            "fecha_nacimiento_responsable": "01/01/1980",
            "sexo_responsable": "F",
            "domicilio_responsable": "Calle Resp 123",
            "localidad_responsable": "Centro",
        },
        mensaje_error="localidad 999999 no encontrado",
    )

    client.force_login(user)
    response = client.get(reverse("expediente_detail", args=[expediente.pk]))

    assert response.status_code == 200
    content = response.content.decode()
    assert re.search(
        rf'name="sexo".*?option value="{sexo_m.pk}"\s+selected',
        content,
        flags=re.DOTALL,
    )
    assert re.search(
        rf'name="sexo_responsable".*?option value="{sexo_f.pk}"\s+selected',
        content,
        flags=re.DOTALL,
    )


@pytest.mark.django_db
def test_actualizar_registro_erroneo_rechaza_campos_obligatorios_faltantes(client):
    user, provincia = _crear_usuario_provincial("prov_update")
    user.is_superuser = True
    user.save(update_fields=["is_superuser"])
    expediente = _crear_contexto_expediente(user)
    registro = RegistroErroneo.objects.create(
        expediente=expediente,
        fila_excel=2,
        datos_raw={
            "apellido": "Perez",
            "nombre": "Ana",
            "documento": "12345678",
            "fecha_nacimiento": "01/01/2010",
            "sexo": "1",
            "nacionalidad": "1",
            "municipio": "1",
            "localidad": "1",
            "calle": "Calle 1",
            "altura": "123",
            "codigo_postal": "1000",
            "apellido_responsable": "Gomez",
            "nombre_responsable": "Laura",
            "documento_responsable": "20123456789",
            "fecha_nacimiento_responsable": "01/01/1980",
            "sexo_responsable": "2",
            "domicilio_responsable": "Calle Resp 123",
            "localidad_responsable": "Centro",
        },
        mensaje_error="Faltan campos obligatorios: sexo",
    )

    payload = dict(registro.datos_raw)
    payload["sexo"] = ""

    client.force_login(user)
    response = client.post(
        reverse("registro_erroneo_actualizar", args=[expediente.pk, registro.pk]),
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == 400
    assert "sexo" in response.json()["error"].lower()
    assert response.json()["saved_partial"] is True

    registro.refresh_from_db()
    assert registro.datos_raw["sexo"] == "1"
    assert "sexo" in registro.mensaje_error.lower()


@pytest.mark.django_db
def test_actualizar_registro_erroneo_mergea_campos_omitidos_y_conserva_sexo(client):
    user, provincia = _crear_usuario_provincial("prov_update_partial")
    user.is_superuser = True
    user.save(update_fields=["is_superuser"])
    expediente = _crear_contexto_expediente(user)
    municipio = Municipio.objects.create(nombre="La Plata", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Centro", municipio=municipio)
    Nacionalidad.objects.create(nacionalidad="Argentina")
    Sexo.objects.create(sexo="Masculino")
    Sexo.objects.create(sexo="Femenino")
    registro = RegistroErroneo.objects.create(
        expediente=expediente,
        fila_excel=2,
        datos_raw={
            "apellido": "Perez",
            "nombre": "Ana",
            "documento": "30123456789",
            "fecha_nacimiento": "01/01/2010",
            "sexo": "1",
            "nacionalidad": "1",
            "municipio": str(municipio.pk),
            "localidad": str(localidad.pk),
            "calle": "Calle 1",
            "altura": "123",
            "codigo_postal": "1000",
            "apellido_responsable": "Gomez",
            "nombre_responsable": "Laura",
            "documento_responsable": "20123456789",
            "fecha_nacimiento_responsable": "01/01/1980",
            "sexo_responsable": "2",
            "domicilio_responsable": "Calle Resp 123",
            "localidad_responsable": localidad.nombre,
        },
        mensaje_error="Localidad inválida",
    )

    client.force_login(user)
    response = client.post(
        reverse("registro_erroneo_actualizar", args=[expediente.pk, registro.pk]),
        data=json.dumps({"localidad": str(localidad.pk)}),
        content_type="application/json",
    )

    assert response.status_code == 200
    registro.refresh_from_db()
    assert registro.datos_raw["localidad"] == str(localidad.pk)
    assert registro.datos_raw["sexo"] == "1"


@pytest.mark.django_db
def test_actualizar_registro_erroneo_permite_borrar_ultimo_dato_responsable(client):
    user, provincia = _crear_usuario_provincial("prov_update_clear_resp")
    user.is_superuser = True
    user.save(update_fields=["is_superuser"])
    expediente = _crear_contexto_expediente(user)
    municipio = Municipio.objects.create(nombre="La Plata", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Centro", municipio=municipio)
    Nacionalidad.objects.create(nacionalidad="Argentina")
    Sexo.objects.create(sexo="Masculino")
    Sexo.objects.create(sexo="Femenino")
    registro = RegistroErroneo.objects.create(
        expediente=expediente,
        fila_excel=2,
        datos_raw={
            "apellido": "Perez",
            "nombre": "Ana",
            "documento": "30123456789",
            "fecha_nacimiento": "01/01/1995",
            "sexo": "1",
            "nacionalidad": "1",
            "municipio": str(municipio.pk),
            "localidad": str(localidad.pk),
            "calle": "Calle 1",
            "altura": "123",
            "codigo_postal": "1000",
            "telefono_responsable": "3415550000",
        },
        mensaje_error="Faltan campos obligatorios del responsable",
    )

    client.force_login(user)
    response = client.post(
        reverse("registro_erroneo_actualizar", args=[expediente.pk, registro.pk]),
        data=json.dumps({"telefono_responsable": ""}),
        content_type="application/json",
    )

    assert response.status_code == 200

    registro.refresh_from_db()
    assert "telefono_responsable" not in registro.datos_raw
    assert all(
        campo not in registro.datos_raw
        for campo in (
            "apellido_responsable",
            "nombre_responsable",
            "documento_responsable",
            "fecha_nacimiento_responsable",
            "sexo_responsable",
            "domicilio_responsable",
            "localidad_responsable",
            "email_responsable",
        )
    )


@pytest.mark.django_db
def test_importacion_con_sexo_responsable_invalido_no_crea_legajo_parcial():
    user, provincia = _crear_usuario_provincial("prov_resp_invalid")
    expediente = _crear_contexto_expediente(user)
    EstadoLegajo.objects.create(nombre="DOCUMENTO_PENDIENTE")
    Sexo.objects.create(sexo="Masculino")
    Sexo.objects.create(sexo="Femenino")
    Nacionalidad.objects.create(nacionalidad="Argentina")
    municipio = Municipio.objects.create(nombre="La Plata", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Centro", municipio=municipio)

    archivo = _crear_archivo_excel(
        headers=[
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
        ],
        row=[
            "Perez",
            "Ana",
            "30123456789",
            "01/01/2010",
            "F",
            "Argentina",
            municipio.pk,
            localidad.pk,
            "Calle 1",
            "123",
            "1000",
            "3415550000",
            "ana@example.com",
            "Gomez",
            "Laura",
            "20123456789",
            "01/01/1980",
            "X",
            "Calle Resp 123",
            localidad.nombre,
            "",
            "",
        ],
    )

    resultado = ImportacionService.importar_legajos_desde_excel(
        expediente=expediente,
        archivo_excel=archivo,
        usuario=user,
    )

    assert resultado["validos"] == 0
    assert resultado["errores"] == 1
    assert ExpedienteCiudadano.objects.count() == 0

    registro = RegistroErroneo.objects.get(expediente=expediente)
    assert "sexo responsable" in registro.mensaje_error.lower()
    assert registro.datos_raw["sexo_responsable"] == "X"


@pytest.mark.django_db
def test_importacion_menor_sin_responsable_genera_error():
    user, provincia = _crear_usuario_provincial("prov_menor_sin_resp")
    expediente = _crear_contexto_expediente(user)
    EstadoLegajo.objects.create(nombre="DOCUMENTO_PENDIENTE")
    Sexo.objects.create(sexo="Masculino")
    Sexo.objects.create(sexo="Femenino")
    Nacionalidad.objects.create(nacionalidad="Argentina")
    municipio = Municipio.objects.create(nombre="La Plata", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Centro", municipio=municipio)

    archivo = _crear_archivo_excel(
        headers=[
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
        ],
        row=[
            "Perez",
            "Ana",
            "30123456789",
            _fecha_hace_anos(10),
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
        ],
    )

    resultado = ImportacionService.importar_legajos_desde_excel(
        expediente=expediente,
        archivo_excel=archivo,
        usuario=user,
    )

    assert resultado["validos"] == 0
    assert resultado["errores"] == 1
    assert ExpedienteCiudadano.objects.count() == 0

    registro = RegistroErroneo.objects.get(expediente=expediente)
    assert "debe tener un responsable" in registro.mensaje_error.lower()


@pytest.mark.django_db
def test_importacion_mayor_con_datos_parciales_de_responsable_exige_completar_obligatorios():
    user, provincia = _crear_usuario_provincial("prov_mayor_resp_parcial")
    expediente = _crear_contexto_expediente(user)
    EstadoLegajo.objects.create(nombre="DOCUMENTO_PENDIENTE")
    Sexo.objects.create(sexo="Masculino")
    Sexo.objects.create(sexo="Femenino")
    Nacionalidad.objects.create(nacionalidad="Argentina")
    municipio = Municipio.objects.create(nombre="La Plata", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Centro", municipio=municipio)

    archivo = _crear_archivo_excel(
        headers=[
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
        ],
        row=[
            "Perez",
            "Ana",
            "30123456789",
            _fecha_hace_anos(25),
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
            "3415550000",
            "",
        ],
    )

    resultado = ImportacionService.importar_legajos_desde_excel(
        expediente=expediente,
        archivo_excel=archivo,
        usuario=user,
    )

    assert resultado["validos"] == 0
    assert resultado["errores"] == 1
    assert ExpedienteCiudadano.objects.count() == 0

    registro = RegistroErroneo.objects.get(expediente=expediente)
    mensaje = registro.mensaje_error.lower()
    assert "faltan campos obligatorios" in mensaje
    assert "apellido_responsable" in mensaje
    assert "documento_responsable" in mensaje


@pytest.mark.django_db
def test_importacion_mayor_sin_responsable_sigue_permitida():
    user, provincia = _crear_usuario_provincial("prov_mayor_sin_resp")
    expediente = _crear_contexto_expediente(user)
    EstadoLegajo.objects.create(nombre="DOCUMENTO_PENDIENTE")
    Sexo.objects.create(sexo="Masculino")
    Sexo.objects.create(sexo="Femenino")
    Nacionalidad.objects.create(nacionalidad="Argentina")
    municipio = Municipio.objects.create(nombre="La Plata", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Centro", municipio=municipio)

    archivo = _crear_archivo_excel(
        headers=[
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
        ],
        row=[
            "Perez",
            "Ana",
            "30123456789",
            _fecha_hace_anos(30),
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
        ],
    )

    resultado = ImportacionService.importar_legajos_desde_excel(
        expediente=expediente,
        archivo_excel=archivo,
        usuario=user,
    )

    assert resultado["validos"] == 1
    assert resultado["errores"] == 0

    legajo = ExpedienteCiudadano.objects.get(expediente=expediente)
    assert legajo.rol == ExpedienteCiudadano.ROLE_BENEFICIARIO


@pytest.mark.django_db
def test_actualizar_registro_erroneo_rechaza_email_responsable_invalido(client):
    user, provincia = _crear_usuario_provincial("prov_update_email")
    user.is_superuser = True
    user.save(update_fields=["is_superuser"])
    expediente = _crear_contexto_expediente(user)
    municipio = Municipio.objects.create(nombre="La Plata", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Centro", municipio=municipio)
    Nacionalidad.objects.create(nacionalidad="Argentina")
    Sexo.objects.create(sexo="Masculino")
    Sexo.objects.create(sexo="Femenino")
    registro = RegistroErroneo.objects.create(
        expediente=expediente,
        fila_excel=2,
        datos_raw={
            "apellido": "Perez",
            "nombre": "Ana",
            "documento": "30123456789",
            "fecha_nacimiento": "01/01/2010",
            "sexo": "1",
            "nacionalidad": "1",
            "municipio": str(municipio.pk),
            "localidad": str(localidad.pk),
            "calle": "Calle 1",
            "altura": "123",
            "codigo_postal": "1000",
            "apellido_responsable": "Gomez",
            "nombre_responsable": "Laura",
            "documento_responsable": "20123456789",
            "fecha_nacimiento_responsable": "01/01/1980",
            "sexo_responsable": "2",
            "domicilio_responsable": "Calle Resp 123",
            "localidad_responsable": localidad.nombre,
            "email_responsable": "laura@example.com",
        },
        mensaje_error="Email responsable inválido",
    )

    payload = dict(registro.datos_raw)
    payload["email_responsable"] = "correo-invalido"

    client.force_login(user)
    response = client.post(
        reverse("registro_erroneo_actualizar", args=[expediente.pk, registro.pk]),
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == 400
    assert "email_responsable" in response.json()["error"].lower()

    registro.refresh_from_db()
    assert registro.datos_raw["email_responsable"] == "laura@example.com"


@pytest.mark.django_db
def test_reprocesar_registro_invalido_no_crea_legajos_parciales(client):
    user, provincia = _crear_usuario_provincial("prov_reprocess_invalid")
    user.is_superuser = True
    user.save(update_fields=["is_superuser"])
    expediente = _crear_contexto_expediente(user)
    EstadoLegajo.objects.create(nombre="DOCUMENTO_PENDIENTE")
    municipio = Municipio.objects.create(nombre="La Plata", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Centro", municipio=municipio)
    Nacionalidad.objects.create(nacionalidad="Argentina")
    Sexo.objects.create(sexo="Masculino")
    Sexo.objects.create(sexo="Femenino")
    registro = RegistroErroneo.objects.create(
        expediente=expediente,
        fila_excel=2,
        datos_raw={
            "apellido": "Perez",
            "nombre": "Ana",
            "documento": "30123456789",
            "fecha_nacimiento": "01/01/2010",
            "sexo": "1",
            "nacionalidad": "1",
            "municipio": str(municipio.pk),
            "localidad": str(localidad.pk),
            "calle": "Calle 1",
            "altura": "123",
            "codigo_postal": "1000",
            "apellido_responsable": "Gomez",
            "nombre_responsable": "Laura",
            "documento_responsable": "20123456789",
            "fecha_nacimiento_responsable": "01/01/1980",
            "sexo_responsable": "2",
            "domicilio_responsable": "Calle Resp 123",
            "localidad_responsable": localidad.nombre,
            "email_responsable": "correo-invalido",
        },
        mensaje_error="Email responsable inválido",
    )

    client.force_login(user)
    response = client.post(
        reverse("registros_erroneos_reprocesar", args=[expediente.pk]),
        data=json.dumps({}),
        content_type="application/json",
    )

    assert response.status_code == 200
    body = response.json()
    assert body["creados"] == 0
    assert body["errores"] == 1
    assert ExpedienteCiudadano.objects.count() == 0

    registro.refresh_from_db()
    assert registro.procesado is False
    assert "email_responsable" in registro.mensaje_error.lower()
