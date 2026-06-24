"""Corrección de la evaluación final de un legajo (Nación autorizada).

- Admin/coordinador pueden cambiar el estado final entre APROBADO/RECHAZADO/SUBSANADO.
- Queda registrado en HistorialValidacionTecnica (usuario, fecha, estados).
- No disponible para usuarios provinciales ni técnicos.
"""

from datetime import date

import pytest
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from ciudadanos.models import Ciudadano
from core.models import Localidad, Municipio, Provincia
from users.models import Profile, ProfileTerritorialScope
from celiaquia.models import (
    EstadoExpediente,
    EstadoLegajo,
    Expediente,
    ExpedienteCiudadano,
    HistorialValidacionTecnica,
    RevisionTecnico,
)


def _grant(user, codename, model, name=None):
    content_type = ContentType.objects.get_for_model(model)
    perm, _ = Permission.objects.get_or_create(
        codename=codename,
        content_type=content_type,
        defaults={"name": name or codename},
    )
    user.user_permissions.add(perm)


def _coordinador(username):
    user = User.objects.create_user(username=username, password="pass")
    _grant(user, "view_expediente", Expediente)
    _grant(user, "role_coordinadorceliaquia", User, name="Coordinador Celiaquia")
    return user


def _tecnico(username):
    user = User.objects.create_user(username=username, password="pass")
    _grant(user, "view_expediente", Expediente)
    _grant(user, "role_tecnicoceliaquia", User, name="Tecnico Celiaquia")
    return user


def _provincial(username, provincia):
    user = User.objects.create_user(username=username, password="pass")
    _grant(user, "view_expediente", Expediente)
    _grant(user, "role_provinciaceliaquia", User, name="Provincia Celiaquia")
    profile, _ = Profile.objects.get_or_create(user=user)
    profile.es_usuario_provincial = True
    profile.save()
    ProfileTerritorialScope.objects.create(profile=profile, provincia=provincia)
    return user


def _legajo(owner, revision, doc, provincia=None):
    estado_exp = EstadoExpediente.objects.create(nombre=f"EST_EXP_{doc}")
    estado_legajo = EstadoLegajo.objects.create(nombre=f"EST_LEG_{doc}")
    expediente = Expediente.objects.create(usuario_provincia=owner, estado=estado_exp)
    ciudadano = Ciudadano.objects.create(
        apellido="Test",
        nombre="Corregir",
        documento=doc,
        fecha_nacimiento=date(1990, 1, 1),
        provincia=provincia,
    )
    legajo = ExpedienteCiudadano.objects.create(
        expediente=expediente,
        ciudadano=ciudadano,
        estado=estado_legajo,
        revision_tecnico=revision,
    )
    return expediente, legajo


@pytest.mark.django_db
def test_coord_corrige_aprobado_a_rechazado(client):
    coord = _coordinador("coord-corr")
    expediente, legajo = _legajo(coord, RevisionTecnico.APROBADO, 80001)

    client.force_login(coord)
    response = client.post(
        reverse("legajo_corregir_evaluacion", args=[expediente.pk, legajo.pk]),
        data={"nuevo_estado": "RECHAZADO", "motivo": "Error de carga"},
    )

    assert response.status_code == 200
    assert response.json()["success"] is True
    legajo.refresh_from_db()
    assert legajo.revision_tecnico == RevisionTecnico.RECHAZADO

    hist = HistorialValidacionTecnica.objects.filter(legajo=legajo).latest("creado_en")
    assert hist.estado_anterior == RevisionTecnico.APROBADO
    assert hist.estado_nuevo == RevisionTecnico.RECHAZADO
    assert hist.usuario_id == coord.id
    assert "Corrección de evaluación final" in (hist.motivo or "")


@pytest.mark.django_db
def test_provincia_no_puede_corregir(client):
    provincia = Provincia.objects.create(nombre="BsAs Corr")
    prov_user = _provincial("prov-corr", provincia)
    expediente, legajo = _legajo(
        prov_user, RevisionTecnico.APROBADO, 80002, provincia=provincia
    )

    client.force_login(prov_user)
    response = client.post(
        reverse("legajo_corregir_evaluacion", args=[expediente.pk, legajo.pk]),
        data={"nuevo_estado": "RECHAZADO"},
    )

    assert response.status_code == 403
    legajo.refresh_from_db()
    assert legajo.revision_tecnico == RevisionTecnico.APROBADO


@pytest.mark.django_db
def test_tecnico_no_puede_corregir(client):
    tecnico = _tecnico("tec-corr")
    expediente, legajo = _legajo(tecnico, RevisionTecnico.APROBADO, 80003)

    client.force_login(tecnico)
    response = client.post(
        reverse("legajo_corregir_evaluacion", args=[expediente.pk, legajo.pk]),
        data={"nuevo_estado": "SUBSANADO"},
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_no_se_corrige_legajo_sin_evaluacion_final(client):
    coord = _coordinador("coord-corr-pend")
    expediente, legajo = _legajo(coord, RevisionTecnico.PENDIENTE, 80004)

    client.force_login(coord)
    response = client.post(
        reverse("legajo_corregir_evaluacion", args=[expediente.pk, legajo.pk]),
        data={"nuevo_estado": "APROBADO"},
    )

    assert response.status_code == 400
    legajo.refresh_from_db()
    assert legajo.revision_tecnico == RevisionTecnico.PENDIENTE


@pytest.mark.django_db
def test_no_se_corrige_al_mismo_estado(client):
    coord = _coordinador("coord-corr-same")
    expediente, legajo = _legajo(coord, RevisionTecnico.APROBADO, 80005)

    client.force_login(coord)
    response = client.post(
        reverse("legajo_corregir_evaluacion", args=[expediente.pk, legajo.pk]),
        data={"nuevo_estado": "APROBADO"},
    )

    assert response.status_code == 400
