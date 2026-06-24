"""Comentarios internos: visibles solo para Nación, no para la provincia.

- Nación (técnico/coordinador/admin) puede marcar un comentario como interno.
- Los comentarios internos no se listan para usuarios provinciales.
- Los comentarios no internos siguen siendo visibles para todos.
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
    HistorialComentarios,
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


def _provincial(username, provincia):
    user = User.objects.create_user(username=username, password="pass")
    _grant(user, "view_expediente", Expediente)
    _grant(user, "role_provinciaceliaquia", User, name="Provincia Celiaquia")
    profile, _ = Profile.objects.get_or_create(user=user)
    profile.es_usuario_provincial = True
    profile.save()
    ProfileTerritorialScope.objects.create(profile=profile, provincia=provincia)
    return user


def _expediente_con_legajo(owner, provincia, municipio, localidad, doc):
    estado_exp = EstadoExpediente.objects.create(nombre=f"EST_EXP_{doc}")
    estado_legajo = EstadoLegajo.objects.create(nombre=f"EST_LEG_{doc}")
    expediente = Expediente.objects.create(usuario_provincia=owner, estado=estado_exp)
    ciudadano = Ciudadano.objects.create(
        apellido="Test",
        nombre="Comentario",
        documento=doc,
        fecha_nacimiento=date(1990, 1, 1),
        provincia=provincia,
        municipio=municipio,
        localidad=localidad,
    )
    legajo = ExpedienteCiudadano.objects.create(
        expediente=expediente, ciudadano=ciudadano, estado=estado_legajo
    )
    return expediente, legajo


@pytest.mark.django_db
def test_nacion_crea_comentario_interno(client):
    provincia = Provincia.objects.create(nombre="BsAs Int")
    municipio = Municipio.objects.create(nombre="Cap Int", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Centro Int", municipio=municipio)
    owner = _provincial("owner-int", provincia)
    coord = _coordinador("coord-int")
    expediente, legajo = _expediente_con_legajo(
        owner, provincia, municipio, localidad, 70001
    )

    client.force_login(coord)
    response = client.post(
        reverse("legajo_comentario_create", args=[expediente.pk, legajo.pk]),
        data={"comentario": "Observación interna", "es_interno": "1"},
    )

    assert response.status_code == 200
    assert response.json()["comentario"]["es_interno"] is True
    comentario = HistorialComentarios.objects.get(legajo=legajo)
    assert comentario.es_interno is True


@pytest.mark.django_db
def test_provincia_no_ve_comentarios_internos(client):
    provincia = Provincia.objects.create(nombre="BsAs Prov")
    municipio = Municipio.objects.create(nombre="Cap Prov", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Centro Prov", municipio=municipio)
    prov_user = _provincial("prov-ve", provincia)
    coord = _coordinador("coord-ve")
    expediente, legajo = _expediente_con_legajo(
        prov_user, provincia, municipio, localidad, 70002
    )

    HistorialComentarios.objects.create(
        legajo=legajo,
        tipo_comentario=HistorialComentarios.TIPO_OBSERVACION_GENERAL,
        comentario="Comentario compartido",
        usuario=coord,
        es_interno=False,
    )
    HistorialComentarios.objects.create(
        legajo=legajo,
        tipo_comentario=HistorialComentarios.TIPO_OBSERVACION_GENERAL,
        comentario="Comentario interno secreto",
        usuario=coord,
        es_interno=True,
    )

    url = reverse("legajo_comentarios_list", args=[expediente.pk, legajo.pk])

    # Provincia: solo ve el no interno.
    client.force_login(prov_user)
    resp_prov = client.get(url)
    assert resp_prov.status_code == 200
    textos_prov = [c["texto"] for c in resp_prov.json()["comentarios"]]
    assert "Comentario compartido" in textos_prov
    assert "Comentario interno secreto" not in textos_prov
    assert all(c["es_interno"] is False for c in resp_prov.json()["comentarios"])

    # Nación (coordinador): ve ambos.
    client.force_login(coord)
    resp_coord = client.get(url)
    assert resp_coord.status_code == 200
    textos_coord = [c["texto"] for c in resp_coord.json()["comentarios"]]
    assert "Comentario compartido" in textos_coord
    assert "Comentario interno secreto" in textos_coord
