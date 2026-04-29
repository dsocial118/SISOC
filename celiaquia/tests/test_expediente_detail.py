"""Tests de regresión para detalle de expedientes en Celiaquía."""

import re
from datetime import date

import pytest
from django.contrib.auth.models import Permission, User
from django.urls import reverse

from celiaquia.models import (
    EstadoExpediente,
    EstadoLegajo,
    Expediente,
    ExpedienteCiudadano,
    HistorialValidacionTecnica,
    RevisionTecnico,
)
from core.models import Provincia
from ciudadanos.models import Ciudadano, GrupoFamiliar
from users.models import Profile


def _legajo_row_html(response, legajo_id):
    html = response.content.decode()
    pattern = (
        rf'<tr class="legajo-row"(?:(?!</tr>).)*data-search="{legajo_id} [^"]*"'
        r"(?:(?!</tr>).)*</tr>"
    )
    match = re.search(
        pattern,
        html,
        flags=re.DOTALL,
    )
    assert match is not None
    return match.group(0)


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


@pytest.mark.django_db
def test_expediente_detail_ordena_grupo_familiar_independiente_del_orden_de_carga(
    client,
):
    user = User.objects.create_user(username="prov2", password="pass")
    permission = Permission.objects.get(
        content_type__app_label="celiaquia",
        codename="view_expediente",
    )
    user.user_permissions.add(permission)

    estado_expediente = EstadoExpediente.objects.create(nombre="CREADO_2")
    estado_legajo = EstadoLegajo.objects.create(nombre="DOCUMENTO_PENDIENTE_2")
    expediente = Expediente.objects.create(
        usuario_provincia=user,
        estado=estado_expediente,
    )

    abuelo = Ciudadano.objects.create(
        apellido="Perez",
        nombre="Roberto",
        fecha_nacimiento=date(1970, 1, 1),
        documento=22345670,
    )
    padre = Ciudadano.objects.create(
        apellido="Perez",
        nombre="Carlos",
        fecha_nacimiento=date(1995, 1, 1),
        documento=22345671,
    )
    hijo = Ciudadano.objects.create(
        apellido="Perez",
        nombre="Tomas",
        fecha_nacimiento=date(2018, 1, 1),
        documento=22345672,
    )

    legajo_hijo = ExpedienteCiudadano.objects.create(
        expediente=expediente,
        ciudadano=hijo,
        estado=estado_legajo,
        rol=ExpedienteCiudadano.ROLE_BENEFICIARIO,
    )
    legajo_padre = ExpedienteCiudadano.objects.create(
        expediente=expediente,
        ciudadano=padre,
        estado=estado_legajo,
        rol=ExpedienteCiudadano.ROLE_BENEFICIARIO_Y_RESPONSABLE,
    )
    legajo_abuelo = ExpedienteCiudadano.objects.create(
        expediente=expediente,
        ciudadano=abuelo,
        estado=estado_legajo,
        rol=ExpedienteCiudadano.ROLE_RESPONSABLE,
    )

    GrupoFamiliar.objects.create(
        ciudadano_1=abuelo,
        ciudadano_2=padre,
        vinculo=GrupoFamiliar.RELACION_PADRE,
        conviven=True,
        cuidador_principal=True,
        estado_relacion=GrupoFamiliar.ESTADO_BUENO,
    )
    GrupoFamiliar.objects.create(
        ciudadano_1=padre,
        ciudadano_2=hijo,
        vinculo=GrupoFamiliar.RELACION_PADRE,
        conviven=True,
        cuidador_principal=True,
        estado_relacion=GrupoFamiliar.ESTADO_BUENO,
    )

    client.force_login(user)
    response = client.get(reverse("expediente_detail", args=[expediente.pk]))

    assert response.status_code == 200
    legajos_ids = [item.pk for item in response.context["legajos_enriquecidos"]]
    assert legajos_ids == [legajo_abuelo.pk, legajo_padre.pk, legajo_hijo.pk]


@pytest.mark.django_db
def test_expediente_detail_expone_motivo_rechazo_para_provincia(client):
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    user = User.objects.create_user(username="prov_rechazo", password="pass")
    permission = Permission.objects.get(
        content_type__app_label="celiaquia",
        codename="view_expediente",
    )
    user.user_permissions.add(permission)
    profile, _ = Profile.objects.get_or_create(user=user)
    profile.es_usuario_provincial = True
    profile.provincia = provincia
    profile.save()

    estado_expediente = EstadoExpediente.objects.create(nombre="EN_ESPERA")
    estado_legajo = EstadoLegajo.objects.create(nombre="DOCUMENTO_PENDIENTE_3")
    expediente = Expediente.objects.create(
        usuario_provincia=user,
        estado=estado_expediente,
    )
    ciudadano = Ciudadano.objects.create(
        apellido="Perez",
        nombre="Lucia",
        fecha_nacimiento=date(2005, 5, 1),
        documento=33444555,
    )
    legajo = ExpedienteCiudadano.objects.create(
        expediente=expediente,
        ciudadano=ciudadano,
        estado=estado_legajo,
        revision_tecnico=RevisionTecnico.RECHAZADO,
    )
    HistorialValidacionTecnica.objects.create(
        legajo=legajo,
        estado_anterior=RevisionTecnico.PENDIENTE,
        estado_nuevo=RevisionTecnico.RECHAZADO,
        usuario=user,
        motivo="Documento ilegible",
    )

    client.force_login(user)
    response = client.get(reverse("expediente_detail", args=[expediente.pk]))

    assert response.status_code == 200
    legajo_ctx = response.context["legajos_enriquecidos"][0]
    assert legajo_ctx.observacion_tecnica_titulo == "Motivo del Rechazo"
    assert legajo_ctx.observacion_tecnica_texto == "Documento ilegible"
    row_html = _legajo_row_html(response, legajo.pk)
    assert "Motivo del Rechazo" in row_html
    assert "Documento ilegible" in row_html
    assert "Motivo del Rechazo" in response.content.decode()
    assert "Documento ilegible" in response.content.decode()


@pytest.mark.django_db
def test_expediente_detail_expone_motivo_rechazo_para_tecnico(client):
    user = User.objects.create_user(username="tecnico_rechazo", password="pass")
    permission = Permission.objects.get(
        content_type__app_label="celiaquia",
        codename="view_expediente",
    )
    user.user_permissions.add(permission)

    estado_expediente = EstadoExpediente.objects.create(nombre="EN_ESPERA_TEC")
    estado_legajo = EstadoLegajo.objects.create(nombre="DOCUMENTO_PENDIENTE_TEC")
    expediente = Expediente.objects.create(
        usuario_provincia=user,
        estado=estado_expediente,
    )
    ciudadano = Ciudadano.objects.create(
        apellido="Gomez",
        nombre="Mario",
        fecha_nacimiento=date(1992, 7, 10),
        documento=30111222,
    )
    legajo = ExpedienteCiudadano.objects.create(
        expediente=expediente,
        ciudadano=ciudadano,
        estado=estado_legajo,
        revision_tecnico=RevisionTecnico.RECHAZADO,
    )
    HistorialValidacionTecnica.objects.create(
        legajo=legajo,
        estado_anterior=RevisionTecnico.PENDIENTE,
        estado_nuevo=RevisionTecnico.RECHAZADO,
        usuario=user,
        motivo="Falta certificado",
    )

    client.force_login(user)
    response = client.get(reverse("expediente_detail", args=[expediente.pk]))

    assert response.status_code == 200
    legajo_ctx = response.context["legajos_enriquecidos"][0]
    assert legajo_ctx.observacion_tecnica_titulo == "Motivo del Rechazo"
    assert legajo_ctx.observacion_tecnica_texto == "Falta certificado"
    row_html = _legajo_row_html(response, legajo.pk)
    assert "Motivo del Rechazo" in row_html
    assert "Falta certificado" in row_html
    assert "Motivo del Rechazo" in response.content.decode()
    assert "Falta certificado" in response.content.decode()
