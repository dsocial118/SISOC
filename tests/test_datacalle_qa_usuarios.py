"""Revisión QA 2026-09-16 — ítems del módulo de usuarios."""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from core.models import Provincia
from users.services import UsuariosService


@pytest.fixture
def provincia(db):
    return Provincia.objects.create(nombre="Córdoba")


def _coordinador_datacalle(provincia, username="coord_dc"):
    """Coordinador tal como lo crea un administrador: grupo + alcance."""
    from django.contrib.auth.models import Permission

    user = get_user_model().objects.create_user(
        username=username, email=f"{username}@example.com", password="Sisoc12345!"
    )
    grupo, _ = Group.objects.get_or_create(name="Coordinador DataCalle")
    grupo.permissions.add(
        *Permission.objects.filter(
            content_type__app_label="datacalle",
            codename__in=["view_relevamiento", "change_relevamiento"],
        )
    )
    user.groups.add(grupo)
    user.profile.es_usuario_provincial = True
    user.profile.save()
    user.profile.territorial_scopes.create(provincia=provincia)
    return user


def _entrevistador(provincia, username="entrev_dc"):
    user = get_user_model().objects.create_user(
        username=username, email=f"{username}@example.com", password="Sisoc12345!"
    )
    user.profile.es_relevador_calle = True
    user.profile.datacalle_rol = "entrevistador"
    user.profile.save()
    user.profile.relevador_calle_provincias.create(provincia=provincia)
    return user


def _visibles(actor, rf):
    request = rf.get("/usuarios/")
    request.user = actor
    return sorted(u.username for u in UsuariosService.get_usuarios_en_alcance(request))


@pytest.mark.django_db
def test_qa_0018_el_coordinador_ve_a_sus_entrevistadores(rf, provincia):
    """QA-0018: el usuario recién creado tiene que aparecer en el listado."""
    coordinador = _coordinador_datacalle(provincia)
    entrevistador = _entrevistador(provincia)

    visibles = _visibles(coordinador, rf)

    assert entrevistador.username in visibles
    assert coordinador.username in visibles


@pytest.mark.django_db
def test_qa_0018_no_ve_entrevistadores_de_otra_provincia(rf, provincia):
    """El alcance nuevo es aditivo pero sigue siendo provincial."""
    otra = Provincia.objects.create(nombre="Salta")
    coordinador = _coordinador_datacalle(provincia)
    ajeno = _entrevistador(otra, "entrev_ajeno")

    assert ajeno.username not in _visibles(coordinador, rf)


@pytest.mark.django_db
def test_qa_0018_no_ve_usuarios_sin_rol_datacalle(rf, provincia):
    """La regla no abre la puerta a todos los usuarios sin grupo."""
    coordinador = _coordinador_datacalle(provincia)
    comun = get_user_model().objects.create_user(
        username="usuario_comun", email="c@example.com", password="Sisoc12345!"
    )

    assert comun.username not in _visibles(coordinador, rf)


@pytest.mark.django_db
def test_el_alcance_de_los_demas_roles_no_cambia(rf, provincia):
    """Un actor sin permisos de DataCalle sigue con el deny-by-default."""
    otro = get_user_model().objects.create_user(
        username="otro_rol", email="o@example.com", password="Sisoc12345!"
    )
    _entrevistador(provincia, "entrev_invisible")

    assert _visibles(otro, rf) == ["otro_rol"]


@pytest.mark.django_db
def test_qa_0014_el_coordinador_ve_un_menu_acotado(client, provincia):
    """El menú muestra Situación de Calle y esconde el resto del backoffice."""
    coordinador = _coordinador_datacalle(provincia, "coord_menu")
    client.force_login(coordinador)

    respuesta = client.get("/inicio/")

    assert respuesta.status_code == 200
    html = respuesta.content.decode()
    assert "Situación de Calle" in html
    assert "Relevamientos DataCalle" in html
    # Módulos ajenos al operativo: no tienen por qué aparecerle.
    assert "Comunicados" not in html
    assert "Configuración de Comedores" not in html
    # Usuarios sí: el coordinador da de alta a sus entrevistadores (QA-0016).
    assert "usuarios" in html.lower()


@pytest.mark.django_db
def test_qa_0014_un_usuario_del_backoffice_conserva_su_menu(client, provincia):
    """La regla sólo aplica al coordinador puro de DataCalle."""
    from django.contrib.auth.models import Permission

    usuario = _coordinador_datacalle(provincia, "coord_mixto")
    # Además gestiona comedores: es un usuario del backoffice, no sólo DataCalle.
    usuario.user_permissions.add(
        Permission.objects.get(
            content_type__app_label="comedores", codename="view_comedor"
        )
    )
    client.force_login(usuario)

    respuesta = client.get("/inicio/")

    assert respuesta.status_code == 200
    assert "Comunicados" in respuesta.content.decode()
