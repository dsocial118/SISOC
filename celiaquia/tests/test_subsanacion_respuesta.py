"""Fase 2: respuesta de la provincia con múltiples archivos.

La provincia adjunta varios archivos a la subsanación activa; se guardan como
SubsanacionArchivo (evidencia nueva) sin reemplazar los archivos originales del
legajo, y la subsanación queda marcada como RESPONDIDA.
"""

from datetime import date

import pytest
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from ciudadanos.models import Ciudadano
from core.models import Localidad, Municipio, Provincia
from users.models import Profile, ProfileTerritorialScope
from celiaquia.models import (
    EstadoExpediente,
    EstadoLegajo,
    Expediente,
    ExpedienteCiudadano,
    RevisionTecnico,
    Subsanacion,
    SubsanacionArchivo,
    SubsanacionEstado,
    SubsanacionObservacion,
)


def _grant(user, codename, model, name=None):
    content_type = ContentType.objects.get_for_model(model)
    perm, _ = Permission.objects.get_or_create(
        codename=codename,
        content_type=content_type,
        defaults={"name": name or codename},
    )
    user.user_permissions.add(perm)


def _provincial_user(username, provincia):
    user = User.objects.create_user(username=username, password="pass")
    _grant(user, "view_expediente", Expediente)
    _grant(user, "role_provinciaceliaquia", User, name="Provincia Celiaquia")
    profile, _ = Profile.objects.get_or_create(user=user)
    profile.es_usuario_provincial = True
    profile.save()
    ProfileTerritorialScope.objects.create(profile=profile, provincia=provincia)
    return user


@pytest.mark.django_db
def test_provincia_responde_subsanacion_con_multiples_archivos(client):
    provincia = Provincia.objects.create(nombre="Salta Resp")
    municipio = Municipio.objects.create(nombre="Capital Resp", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Centro Resp", municipio=municipio)
    user = _provincial_user("prov-resp-subs", provincia)

    estado_exp = EstadoExpediente.objects.create(nombre="EN_ESPERA")
    estado_legajo = EstadoLegajo.objects.create(nombre="DOCUMENTO_PENDIENTE")
    expediente = Expediente.objects.create(usuario_provincia=user, estado=estado_exp)
    ciudadano = Ciudadano.objects.create(
        apellido="Test",
        nombre="Responder",
        documento=99001,
        fecha_nacimiento=date(1990, 1, 1),
        provincia=provincia,
        municipio=municipio,
        localidad=localidad,
    )
    legajo = ExpedienteCiudadano.objects.create(
        expediente=expediente,
        ciudadano=ciudadano,
        estado=estado_legajo,
        revision_tecnico=RevisionTecnico.SUBSANAR,
        archivo2=SimpleUploadedFile("original2.pdf", b"orig2"),
        archivo3=SimpleUploadedFile("original3.pdf", b"orig3"),
    )
    archivo2_original = legajo.archivo2.name
    archivo3_original = legajo.archivo3.name

    subsanacion = Subsanacion.objects.create(
        legajo=legajo,
        estado=SubsanacionEstado.PENDIENTE,
        motivo_general="Corregir documentación",
        solicitada_por=user,
    )
    SubsanacionObservacion.objects.create(
        subsanacion=subsanacion, tipo="DOCUMENTACION", detalle="DNI frente"
    )

    client.force_login(user)
    response = client.post(
        reverse("subsanacion_responder", args=[expediente.pk, legajo.pk]),
        data={
            "archivos": [
                SimpleUploadedFile("dni_frente.pdf", b"nuevo1"),
                SimpleUploadedFile("biopsia.pdf", b"nuevo2"),
            ],
            "descripcion": "DNI y biopsia corregidos",
        },
    )

    assert response.status_code == 200
    assert response.json().get("success") is True

    # Se crean 2 archivos de evidencia nueva.
    archivos = SubsanacionArchivo.objects.filter(subsanacion=subsanacion)
    assert archivos.count() == 2
    assert all(a.usuario_id == user.id for a in archivos)

    # La subsanación queda RESPONDIDA con usuario y fecha.
    subsanacion.refresh_from_db()
    assert subsanacion.estado == SubsanacionEstado.RESPONDIDA
    assert subsanacion.respondida_por_id == user.id
    assert subsanacion.respondida_en is not None

    # Los archivos originales del legajo NO se reemplazan.
    legajo.refresh_from_db()
    assert legajo.archivo2.name == archivo2_original
    assert legajo.archivo3.name == archivo3_original


@pytest.mark.django_db
def test_responder_sin_subsanacion_pendiente_falla(client):
    provincia = Provincia.objects.create(nombre="Salta Sin")
    municipio = Municipio.objects.create(nombre="Capital Sin", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Centro Sin", municipio=municipio)
    user = _provincial_user("prov-resp-sin", provincia)

    estado_exp = EstadoExpediente.objects.create(nombre="EN_ESPERA")
    estado_legajo = EstadoLegajo.objects.create(nombre="DOCUMENTO_PENDIENTE")
    expediente = Expediente.objects.create(usuario_provincia=user, estado=estado_exp)
    ciudadano = Ciudadano.objects.create(
        apellido="Test",
        nombre="SinSubs",
        documento=99002,
        fecha_nacimiento=date(1990, 1, 1),
        provincia=provincia,
        municipio=municipio,
        localidad=localidad,
    )
    # Legajo en SUBSANAR pero sin objeto Subsanacion pendiente.
    legajo = ExpedienteCiudadano.objects.create(
        expediente=expediente,
        ciudadano=ciudadano,
        estado=estado_legajo,
        revision_tecnico=RevisionTecnico.SUBSANAR,
    )

    client.force_login(user)
    response = client.post(
        reverse("subsanacion_responder", args=[expediente.pk, legajo.pk]),
        data={"archivos": [SimpleUploadedFile("x.pdf", b"x")]},
    )

    assert response.status_code == 400
    assert response.json().get("success") is False
    assert SubsanacionArchivo.objects.count() == 0
