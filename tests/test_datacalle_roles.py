"""Tests de los tres roles de DataCalle (decisión 2026-09-18)."""

import pytest
from django.contrib.auth import get_user_model

from core.models import Provincia
from users.models import Profile, RelevadorCalleProvincia
from users.services_datacalle import (
    es_administrador_datacalle,
    es_coordinador_datacalle,
    es_solo_app,
    get_datacalle_provincia_ids,
    get_datacalle_rol,
    get_relevador_calle_provincias,
    get_relevador_calle_users_for_provincia,
    tiene_acceso_datacalle,
)


@pytest.fixture
def provincia(db):
    return Provincia.objects.create(nombre="Córdoba")


def test_existen_los_tres_roles_del_documento_funcional():
    codigos = [codigo for codigo, _ in Profile.DataCalleRol.choices]
    assert codigos == ["administrador", "coordinador", "entrevistador"]


def test_las_etiquetas_son_las_del_documento_funcional():
    etiquetas = dict(Profile.DataCalleRol.choices)
    assert etiquetas["administrador"] == "Administrador Nacional"
    assert etiquetas["coordinador"] == "Coordinador Provincial"
    assert etiquetas["entrevistador"] == "Relevador"


def _usuario(username, rol, provincia=None, staff=False):
    user = get_user_model().objects.create_user(
        username=username, email=f"{username}@example.com", password="Sisoc12345!"
    )
    user.is_staff = staff
    user.save()
    perfil = user.profile
    perfil.datacalle_rol = rol
    perfil.es_relevador_calle = bool(rol)
    if rol == "coordinador" and provincia is not None:
        perfil.es_usuario_provincial = True
    perfil.save()
    if provincia is not None:
        if rol == "entrevistador":
            RelevadorCalleProvincia.objects.create(profile=perfil, provincia=provincia)
        else:
            perfil.territorial_scopes.create(provincia=provincia)
    return user


@pytest.mark.django_db
def test_la_jerarquia_es_decreciente(provincia):
    admin = _usuario("admin_dc", "administrador", staff=True)
    coord = _usuario("coord_dc", "coordinador", provincia, staff=True)
    relevador = _usuario("relev_dc", "entrevistador", provincia)

    # Los tres acceden a la app.
    assert [tiene_acceso_datacalle(u) for u in (admin, coord, relevador)] == [
        True,
        True,
        True,
    ]
    # Coordinador incluye al administrador: el superior puede lo del inferior.
    assert es_coordinador_datacalle(admin) is True
    assert es_coordinador_datacalle(coord) is True
    assert es_coordinador_datacalle(relevador) is False
    # Administrador es solo el administrador.
    assert es_administrador_datacalle(admin) is True
    assert es_administrador_datacalle(coord) is False
    # Solo-app es solo el relevador: es quien no entra a SISOC.
    assert [es_solo_app(u) for u in (admin, coord, relevador)] == [False, False, True]


@pytest.mark.django_db
def test_el_administrador_no_tiene_restriccion_territorial(provincia):
    admin = _usuario("admin_terr", "administrador", staff=True)
    coord = _usuario("coord_terr", "coordinador", provincia, staff=True)
    relevador = _usuario("relev_terr", "entrevistador", provincia)

    assert get_datacalle_provincia_ids(admin) is None
    assert get_datacalle_provincia_ids(coord) == [provincia.id]
    assert get_datacalle_provincia_ids(relevador) == [provincia.id]


@pytest.mark.django_db
def test_un_usuario_sin_rol_no_accede(provincia):
    ajeno = get_user_model().objects.create_user(
        username="ajeno", email="ajeno@example.com", password="Sisoc12345!"
    )

    assert get_datacalle_rol(ajeno) == ""
    assert tiene_acceso_datacalle(ajeno) is False
    assert es_coordinador_datacalle(ajeno) is False
    assert get_datacalle_provincia_ids(ajeno) == []


@pytest.mark.django_db
def test_el_equipo_del_operativo_solo_ofrece_relevadores(provincia):
    """El coordinador tambien lleva el flag ahora: no puede colarse al equipo."""
    relevador = _usuario("relev_equipo", "entrevistador", provincia)
    _usuario("coord_equipo", "coordinador", provincia, staff=True)

    disponibles = get_relevador_calle_users_for_provincia(provincia.id)

    assert [u.username for u in disponibles] == [relevador.username]


@pytest.mark.django_db
def test_las_provincias_del_api_salen_de_donde_corresponde_segun_el_rol(provincia):
    """QA D1.2 (/api/users/me/): el administrador no puede devolver ``[]``.

    Dos provincias para que "todas" (administrador) se distinga de "una sola"
    (coordinador y entrevistador, cada uno con su propio alcance).
    """
    otra_provincia = Provincia.objects.create(nombre="Salta")
    admin = _usuario("admin_prov_api", "administrador", staff=True)
    coord = _usuario("coord_prov_api", "coordinador", provincia, staff=True)
    relevador = _usuario("relev_prov_api", "entrevistador", provincia)

    assert get_relevador_calle_provincias(relevador) == [
        {"id": provincia.id, "nombre": provincia.nombre}
    ]
    assert get_relevador_calle_provincias(coord) == [
        {"id": provincia.id, "nombre": provincia.nombre}
    ]
    assert get_relevador_calle_provincias(admin) == [
        {"id": provincia.id, "nombre": provincia.nombre},
        {"id": otra_provincia.id, "nombre": otra_provincia.nombre},
    ]
