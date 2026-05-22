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
from celiaquia.views import expediente as expediente_view
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
def test_detalle_expediente_no_marca_responsable_como_obligatorio_para_mayor(client):
    user, provincia = _crear_usuario_provincial("prov_detail_adulto")
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
    RegistroErroneo.objects.create(
        expediente=expediente,
        fila_excel=2,
        datos_raw={
            "apellido": "Perez",
            "nombre": "Ana",
            "documento": "12345678",
            "fecha_nacimiento": "01/01/1990",
            "sexo": "Masculino",
            "nacionalidad": "Argentina",
            "municipio": str(municipio.pk),
            "localidad": str(localidad.pk),
            "calle": "Calle 1",
            "altura": "123",
            "codigo_postal": "1000",
            "apellido_responsable": "Gomez",
        },
        mensaje_error="Registro con datos pendientes",
    )

    client.force_login(user)
    response = client.get(reverse("expediente_detail", args=[expediente.pk]))

    assert response.status_code == 200
    content = response.content.decode()
    assert "Apellido Responsable *" not in content
    assert re.search(r'name="apellido_responsable"[^>]*required', content) is None
    assert re.search(r'name="localidad_responsable"[^>]*required', content) is None


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
def test_detalle_expediente_muestra_nacionalidad_editable_y_autocompleta_municipio_por_localidad(
    client,
):
    user, provincia = _crear_usuario_provincial("prov_detail_defaults")
    permission = Permission.objects.get(
        content_type__app_label="celiaquia",
        codename="view_expediente",
    )
    user.user_permissions.add(permission)

    expediente = _crear_contexto_expediente(user)
    municipio = Municipio.objects.create(nombre="La Plata", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Centro", municipio=municipio)
    argentina = Nacionalidad.objects.create(nacionalidad="Argentina")
    Sexo.objects.create(sexo="Masculino")
    registro = RegistroErroneo.objects.create(
        expediente=expediente,
        fila_excel=4,
        datos_raw={
            "apellido": "Perez",
            "nombre": "Ana",
            "documento": "12345678",
            "fecha_nacimiento": "01/01/2010",
            "sexo": "Masculino",
            "localidad": str(localidad.pk),
            "calle": "Calle 1",
            "altura": "123",
            "codigo_postal": "1000",
        },
        mensaje_error="Faltan campos obligatorios: nacionalidad",
    )

    client.force_login(user)
    response = client.get(reverse("expediente_detail", args=[expediente.pk]))

    content = response.content.decode()
    form_pattern = (
        rf'<form[^>]+class="form-editar-error"[^>]+data-registro-id="{registro.pk}"'
        rf".*?</form>"
    )
    form_match = re.search(form_pattern, content, flags=re.DOTALL)

    assert form_match is not None
    form_html = form_match.group(0)
    nacionalidad_select = re.search(
        r'<select[^>]+name="nacionalidad".*?</select>',
        form_html,
        flags=re.DOTALL,
    )
    municipio_select = re.search(
        r'<select[^>]+name="municipio".*?</select>',
        form_html,
        flags=re.DOTALL,
    )
    assert nacionalidad_select is not None
    assert municipio_select is not None
    assert (
        re.search(
            rf'option value="{argentina.pk}"\s+selected',
            nacionalidad_select.group(0),
            flags=re.DOTALL,
        )
        is None
    )
    assert re.search(
        rf'option value="{municipio.pk}"\s+selected',
        municipio_select.group(0),
        flags=re.DOTALL,
    )
    assert 'for="editar-nacionalidad"' in content


@pytest.mark.django_db
def test_detalle_expediente_no_autoselecciona_nacionalidad_invalida_o_vacia(client):
    user, provincia = _crear_usuario_provincial("prov_detail_nacionalidad_sin_default")
    permission = Permission.objects.get(
        content_type__app_label="celiaquia",
        codename="view_expediente",
    )
    user.user_permissions.add(permission)

    expediente = _crear_contexto_expediente(user)
    municipio = Municipio.objects.create(nombre="La Plata", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Centro", municipio=municipio)
    argentina = Nacionalidad.objects.create(nacionalidad="Argentina")
    Sexo.objects.create(sexo="Masculino")
    registro_invalido = RegistroErroneo.objects.create(
        expediente=expediente,
        fila_excel=10,
        datos_raw={
            "apellido": "Perez",
            "nombre": "Ana",
            "documento": "12345678",
            "fecha_nacimiento": "01/01/1990",
            "sexo": "Masculino",
            "nacionalidad": "per",
            "municipio": str(municipio.pk),
            "localidad": str(localidad.pk),
            "calle": "Calle 1",
            "altura": "123",
            "codigo_postal": "1000",
        },
        mensaje_error="Nacionalidad inválida: per",
    )
    registro_vacio = RegistroErroneo.objects.create(
        expediente=expediente,
        fila_excel=11,
        datos_raw={
            "apellido": "Lopez",
            "nombre": "Juan",
            "documento": "87654321",
            "fecha_nacimiento": "01/01/1990",
            "sexo": "Masculino",
            "municipio": str(municipio.pk),
            "localidad": str(localidad.pk),
            "calle": "Calle 2",
            "altura": "456",
            "codigo_postal": "1000",
        },
        mensaje_error="Faltan campos obligatorios: nacionalidad",
    )

    client.force_login(user)
    response = client.get(reverse("expediente_detail", args=[expediente.pk]))

    assert response.status_code == 200
    content = response.content.decode()
    for registro in (registro_invalido, registro_vacio):
        form_pattern = (
            rf'<form[^>]+class="form-editar-error"[^>]+data-registro-id="{registro.pk}"'
            rf".*?</form>"
        )
        form_match = re.search(form_pattern, content, flags=re.DOTALL)
        assert form_match is not None
        form_html = form_match.group(0)
        nacionalidad_select = re.search(
            r'<select[^>]+name="nacionalidad".*?</select>',
            form_html,
            flags=re.DOTALL,
        )
        assert nacionalidad_select is not None
        assert (
            re.search(
                rf'option value="{argentina.pk}"\s+selected',
                nacionalidad_select.group(0),
                flags=re.DOTALL,
            )
            is None
        )


@pytest.mark.django_db
def test_detalle_expediente_marca_nacionalidad_invalida_en_campos_invalidos(client):
    user, provincia = _crear_usuario_provincial("prov_detail_invalid_fields")
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
    RegistroErroneo.objects.create(
        expediente=expediente,
        fila_excel=9,
        datos_raw={
            "apellido": "Perez",
            "nombre": "Ana",
            "documento": "12345678",
            "fecha_nacimiento": "01/01/1990",
            "sexo": "Masculino",
            "nacionalidad": "Narnia",
            "municipio": str(municipio.pk),
            "localidad": str(localidad.pk),
            "calle": "Calle 1",
            "altura": "123",
            "codigo_postal": "1000",
        },
        mensaje_error="Nacionalidad inválida: Narnia",
    )

    client.force_login(user)
    response = client.get(reverse("expediente_detail", args=[expediente.pk]))

    assert response.status_code == 200
    content = response.content.decode()
    assert 'data-invalid-fields="nacionalidad"' in content


@pytest.mark.django_db
def test_detalle_expediente_marca_altura_faltante_en_campos_invalidos(client):
    user, provincia = _crear_usuario_provincial("prov_detail_invalid_altura")
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
    RegistroErroneo.objects.create(
        expediente=expediente,
        fila_excel=12,
        datos_raw={
            "apellido": "Perez",
            "nombre": "Ana",
            "documento": "12345678",
            "fecha_nacimiento": "01/01/1990",
            "sexo": "Masculino",
            "nacionalidad": "Argentina",
            "municipio": str(municipio.pk),
            "localidad": str(localidad.pk),
            "calle": "Calle 1",
            "codigo_postal": "1000",
        },
        mensaje_error="Faltan campos obligatorios: altura",
    )

    client.force_login(user)
    response = client.get(reverse("expediente_detail", args=[expediente.pk]))

    assert response.status_code == 200
    content = response.content.decode()
    assert 'data-invalid-fields="altura"' in content


@pytest.mark.django_db
def test_detalle_expediente_autocompleta_nacionalidad_desde_pais_relacionado(client):
    user, provincia = _crear_usuario_provincial("prov_detail_country_mapping")
    permission = Permission.objects.get(
        content_type__app_label="celiaquia",
        codename="view_expediente",
    )
    user.user_permissions.add(permission)

    expediente = _crear_contexto_expediente(user)
    municipio = Municipio.objects.create(nombre="La Plata", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Centro", municipio=municipio)
    brasileña = Nacionalidad.objects.create(nacionalidad="Brasileña")
    Sexo.objects.create(sexo="Masculino")
    RegistroErroneo.objects.create(
        expediente=expediente,
        fila_excel=8,
        datos_raw={
            "apellido": "Silva",
            "nombre": "Ana",
            "documento": "12345678",
            "fecha_nacimiento": "01/01/1990",
            "sexo": "Masculino",
            "nacionalidad": "Brasil",
            "municipio": str(municipio.pk),
            "localidad": str(localidad.pk),
            "calle": "Calle 1",
            "altura": "123",
            "codigo_postal": "1000",
        },
        mensaje_error="Revision manual requerida",
    )

    client.force_login(user)
    response = client.get(reverse("expediente_detail", args=[expediente.pk]))

    assert response.status_code == 200
    content = response.content.decode()
    assert re.search(
        rf'name="nacionalidad".*?option value="{brasileña.pk}"\s+selected',
        content,
        flags=re.DOTALL,
    )


def test_campos_invalidos_desde_mensaje_error_soporta_prefijo_reproceso():
    invalid_fields = expediente_view._campos_invalidos_desde_mensaje_error(
        "Error al reprocesar: Faltan campos obligatorios: apellido, nombre"
    )

    assert invalid_fields == ["apellido", "nombre"]


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
    assert response.json()["invalid_fields"] == ["sexo"]

    registro.refresh_from_db()
    assert registro.datos_raw["sexo"] == "1"
    assert "sexo" in registro.mensaje_error.lower()


@pytest.mark.django_db
def test_actualizar_registro_erroneo_informa_invalid_fields_para_validation_error_compuesto(
    client,
):
    user, provincia = _crear_usuario_provincial("prov_update_invalid_fields_multiple")
    user.is_superuser = True
    user.save(update_fields=["is_superuser"])
    expediente = _crear_contexto_expediente(user)
    municipio = Municipio.objects.create(nombre="La Plata", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Centro", municipio=municipio)
    argentina = Nacionalidad.objects.create(nacionalidad="Argentina")
    sexo = Sexo.objects.create(sexo="Masculino")
    registro = RegistroErroneo.objects.create(
        expediente=expediente,
        fila_excel=13,
        datos_raw={
            "apellido": "Perez",
            "nombre": "Ana",
            "documento": "12345678",
            "fecha_nacimiento": "01/01/1990",
            "sexo": str(sexo.pk),
            "nacionalidad": str(argentina.pk),
            "municipio": str(municipio.pk),
            "localidad": str(localidad.pk),
            "calle": "Calle 1",
            "altura": "123",
            "codigo_postal": "1000",
        },
        mensaje_error="Faltan campos obligatorios: apellido, nombre",
    )

    payload = dict(registro.datos_raw)
    payload["apellido"] = ""
    payload["nombre"] = ""

    client.force_login(user)
    response = client.post(
        reverse("registro_erroneo_actualizar", args=[expediente.pk, registro.pk]),
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.json()["saved_partial"] is True
    assert set(response.json()["invalid_fields"]) == {"apellido", "nombre"}


@pytest.mark.django_db
def test_actualizar_registro_erroneo_permite_mayor_con_responsable_incompleto(client):
    user, provincia = _crear_usuario_provincial("prov_update_adulto")
    user.is_superuser = True
    user.save(update_fields=["is_superuser"])
    expediente = _crear_contexto_expediente(user)
    municipio = Municipio.objects.create(nombre="La Plata", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Centro", municipio=municipio)
    argentina = Nacionalidad.objects.create(nacionalidad="Argentina")
    sexo = Sexo.objects.create(sexo="Masculino")
    registro = RegistroErroneo.objects.create(
        expediente=expediente,
        fila_excel=6,
        datos_raw={
            "apellido": "Perez",
            "nombre": "Ana",
            "documento": "12345678",
            "fecha_nacimiento": "01/01/1990",
            "sexo": str(sexo.pk),
            "nacionalidad": str(argentina.pk),
            "municipio": str(municipio.pk),
            "localidad": str(localidad.pk),
            "calle": "Calle 1",
            "altura": "123",
            "codigo_postal": "1000",
            "apellido_responsable": "Gomez",
        },
        mensaje_error="Faltan campos obligatorios: nombre_responsable",
    )

    payload = dict(registro.datos_raw)

    client.force_login(user)
    response = client.post(
        reverse("registro_erroneo_actualizar", args=[expediente.pk, registro.pk]),
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.json()["success"] is True

    registro.refresh_from_db()
    assert registro.datos_raw["apellido_responsable"] == "Gomez"


@pytest.mark.django_db
def test_actualizar_registro_erroneo_conserva_nacionalidad_elegida_y_corrige_municipio_por_localidad(
    client,
):
    user, provincia = _crear_usuario_provincial("prov_update_defaults")
    user.is_superuser = True
    user.save(update_fields=["is_superuser"])
    expediente = _crear_contexto_expediente(user)
    municipio_origen = Municipio.objects.create(nombre="La Plata", provincia=provincia)
    localidad_origen = Localidad.objects.create(
        nombre="Centro", municipio=municipio_origen
    )
    municipio_destino = Municipio.objects.create(nombre="Berisso", provincia=provincia)
    localidad_destino = Localidad.objects.create(
        nombre="Villa Nueva", municipio=municipio_destino
    )
    argentina = Nacionalidad.objects.create(nacionalidad="Argentina")
    otra_nacionalidad = Nacionalidad.objects.create(nacionalidad="Uruguaya")
    Sexo.objects.create(sexo="Masculino")
    Sexo.objects.create(sexo="Femenino")
    registro = RegistroErroneo.objects.create(
        expediente=expediente,
        fila_excel=5,
        datos_raw={
            "apellido": "Perez",
            "nombre": "Ana",
            "documento": "12345678",
            "fecha_nacimiento": "01/01/1990",
            "sexo": "1",
            "nacionalidad": str(otra_nacionalidad.pk),
            "municipio": str(municipio_origen.pk),
            "localidad": str(localidad_origen.pk),
            "calle": "Calle 1",
            "altura": "123",
            "codigo_postal": "1000",
        },
        mensaje_error="Municipio inconsistente",
    )

    payload = dict(registro.datos_raw)
    payload["nacionalidad"] = str(otra_nacionalidad.pk)
    payload["municipio"] = str(municipio_origen.pk)
    payload["localidad"] = str(localidad_destino.pk)

    client.force_login(user)
    response = client.post(
        reverse("registro_erroneo_actualizar", args=[expediente.pk, registro.pk]),
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == 200
    registro.refresh_from_db()
    assert registro.datos_raw["nacionalidad"] == str(otra_nacionalidad.pk)
    assert registro.datos_raw["municipio"] == str(municipio_destino.pk)
    assert registro.datos_raw["localidad"] == str(localidad_destino.pk)


@pytest.mark.django_db
def test_actualizar_registro_erroneo_permite_corregir_nacionalidad_invalida(client):
    user, provincia = _crear_usuario_provincial("prov_update_nacionalidad")
    user.is_superuser = True
    user.save(update_fields=["is_superuser"])
    expediente = _crear_contexto_expediente(user)
    municipio = Municipio.objects.create(nombre="La Plata", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Centro", municipio=municipio)
    argentina = Nacionalidad.objects.create(nacionalidad="Argentina")
    uruguaya = Nacionalidad.objects.create(nacionalidad="Uruguaya")
    sexo = Sexo.objects.create(sexo="Masculino")
    registro = RegistroErroneo.objects.create(
        expediente=expediente,
        fila_excel=7,
        datos_raw={
            "apellido": "Perez",
            "nombre": "Ana",
            "documento": "12345678",
            "fecha_nacimiento": "01/01/1990",
            "sexo": str(sexo.pk),
            "nacionalidad": "Narnia",
            "municipio": str(municipio.pk),
            "localidad": str(localidad.pk),
            "calle": "Calle 1",
            "altura": "123",
            "codigo_postal": "1000",
        },
        mensaje_error="Nacionalidad invalida: Narnia",
    )

    client.force_login(user)
    response = client.post(
        reverse("registro_erroneo_actualizar", args=[expediente.pk, registro.pk]),
        data=json.dumps({"nacionalidad": str(uruguaya.pk)}),
        content_type="application/json",
    )

    assert response.status_code == 200
    registro.refresh_from_db()
    assert registro.datos_raw["nacionalidad"] == str(uruguaya.pk)


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
            "contacto_responsable",
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
def test_importacion_mayor_con_datos_parciales_de_responsable_no_bloquea_importacion():
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

    assert resultado["validos"] == 1
    assert resultado["errores"] == 0
    assert ExpedienteCiudadano.objects.count() == 1
    assert not RegistroErroneo.objects.filter(expediente=expediente).exists()


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
    assert response.json()["invalid_fields"] == ["email_responsable"]

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
