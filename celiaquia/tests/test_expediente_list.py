"""Tests for test expediente list."""

from datetime import date

import pytest
from django.urls import reverse
from django.contrib.auth.models import Permission, User

from ciudadanos.models import Ciudadano
from users.models import Profile, ProfileTerritorialScope
from core.models import Localidad, Municipio, Provincia
from celiaquia.models import (
    Expediente,
    ExpedienteCiudadano,
    EstadoExpediente,
    EstadoLegajo,
    RevisionTecnico,
)


def _grant_view_expediente(user):
    permission = Permission.objects.get(
        content_type__app_label="celiaquia",
        codename="view_expediente",
    )
    user.user_permissions.add(permission)


@pytest.mark.django_db
def test_expediente_list_displays_id_and_provincia(client):
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    user = User.objects.create_user(username="prov", password="pass")
    permission = Permission.objects.get(
        content_type__app_label="celiaquia",
        codename="view_expediente",
    )
    user.user_permissions.add(permission)
    profile, _ = Profile.objects.get_or_create(user=user)
    profile.es_usuario_provincial = True
    profile.provincia = provincia
    profile.save()
    estado = EstadoExpediente.objects.create(nombre="CREADO")
    expediente = Expediente.objects.create(usuario_provincia=user, estado=estado)

    client.force_login(user)
    response = client.get(reverse("expediente_list"))

    assert response.status_code == 200
    content = response.content.decode()
    assert str(expediente.pk) in content
    assert provincia.nombre in content


def _crear_expediente_con_ciudadano(
    *,
    owner,
    estado,
    documento,
    provincia,
    municipio,
    localidad,
):
    expediente = Expediente.objects.create(usuario_provincia=owner, estado=estado)
    ciudadano = Ciudadano.objects.create(
        apellido="Perez",
        nombre=f"Ciudadano {documento}",
        fecha_nacimiento=date(2010, 1, 1),
        documento=documento,
        provincia=provincia,
        municipio=municipio,
        localidad=localidad,
    )
    estado_legajo, _ = EstadoLegajo.objects.get_or_create(nombre="DOCUMENTO_PENDIENTE")
    ExpedienteCiudadano.objects.create(
        expediente=expediente,
        ciudadano=ciudadano,
        estado=estado_legajo,
    )
    return expediente


@pytest.mark.django_db
def test_expediente_list_scope_municipio_no_muestra_otro_municipio(client):
    provincia = Provincia.objects.create(nombre="Buenos Aires Municipio")
    municipio_visible = Municipio.objects.create(nombre="La Plata", provincia=provincia)
    municipio_oculto = Municipio.objects.create(nombre="Azul", provincia=provincia)
    localidad_visible = Localidad.objects.create(
        nombre="Tolosa",
        municipio=municipio_visible,
    )
    localidad_oculta = Localidad.objects.create(
        nombre="Centro",
        municipio=municipio_oculto,
    )
    user = User.objects.create_user(
        username="prov-municipio-celiaquia", password="pass"
    )
    _grant_view_expediente(user)
    owner = User.objects.create_user(username="owner-celiaquia", password="pass")
    profile = user.profile
    profile.es_usuario_provincial = True
    profile.save()
    ProfileTerritorialScope.objects.create(
        profile=profile,
        provincia=provincia,
        municipio=municipio_visible,
    )
    estado = EstadoExpediente.objects.create(nombre="CREADO")
    expediente_visible = _crear_expediente_con_ciudadano(
        owner=owner,
        estado=estado,
        documento=301,
        provincia=provincia,
        municipio=municipio_visible,
        localidad=localidad_visible,
    )
    expediente_oculto = _crear_expediente_con_ciudadano(
        owner=owner,
        estado=estado,
        documento=302,
        provincia=provincia,
        municipio=municipio_oculto,
        localidad=localidad_oculta,
    )

    client.force_login(user)
    response = client.get(reverse("expediente_list"))
    expedientes = list(response.context["expedientes"])

    assert response.status_code == 200
    assert expediente_visible in expedientes
    assert expediente_oculto not in expedientes


@pytest.mark.django_db
def test_expediente_list_scope_localidad_no_muestra_otra_localidad(client):
    provincia = Provincia.objects.create(nombre="Buenos Aires Localidad")
    municipio = Municipio.objects.create(
        nombre="La Plata Localidad", provincia=provincia
    )
    localidad_visible = Localidad.objects.create(
        nombre="Tolosa Norte", municipio=municipio
    )
    localidad_oculta = Localidad.objects.create(
        nombre="Tolosa Sur", municipio=municipio
    )
    user = User.objects.create_user(
        username="prov-localidad-celiaquia", password="pass"
    )
    _grant_view_expediente(user)
    owner = User.objects.create_user(
        username="owner-localidad-celiaquia", password="pass"
    )
    profile = user.profile
    profile.es_usuario_provincial = True
    profile.save()
    ProfileTerritorialScope.objects.create(
        profile=profile,
        provincia=provincia,
        municipio=municipio,
        localidad=localidad_visible,
    )
    estado = EstadoExpediente.objects.create(nombre="CREADO")
    expediente_visible = _crear_expediente_con_ciudadano(
        owner=owner,
        estado=estado,
        documento=401,
        provincia=provincia,
        municipio=municipio,
        localidad=localidad_visible,
    )
    expediente_oculto = _crear_expediente_con_ciudadano(
        owner=owner,
        estado=estado,
        documento=402,
        provincia=provincia,
        municipio=municipio,
        localidad=localidad_oculta,
    )

    client.force_login(user)
    response = client.get(reverse("expediente_list"))
    expedientes = list(response.context["expedientes"])

    assert response.status_code == 200
    assert expediente_visible in expedientes
    assert expediente_oculto not in expedientes


@pytest.mark.django_db
def test_legajos_subsanar_count_no_cambia_con_busqueda(client):
    """Regresión: el contador de legajos A Subsanar debe ser consistente
    con o sin filtro de búsqueda (el JOIN del filtro no debe contaminar el Count)."""
    provincia = Provincia.objects.create(nombre="Córdoba Subsanar")
    municipio = Municipio.objects.create(nombre="Capital", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Centro", municipio=municipio)
    admin = User.objects.create_superuser(username="admin-subsanar", password="pass")
    owner = User.objects.create_user(username="owner-subsanar", password="pass")

    estado_exp = EstadoExpediente.objects.create(nombre="ASIGNADO_SUBSANAR")
    estado_legajo, _ = EstadoLegajo.objects.get_or_create(nombre="DOCUMENTO_PENDIENTE")
    expediente = Expediente.objects.create(usuario_provincia=owner, estado=estado_exp)

    def _ciudadano(doc):
        return Ciudadano.objects.create(
            apellido="Test",
            nombre=f"Ciudadano {doc}",
            fecha_nacimiento=date(2010, 1, 1),
            documento=doc,
            provincia=provincia,
            municipio=municipio,
            localidad=localidad,
        )

    c1 = _ciudadano(501)
    c2 = _ciudadano(502)
    ExpedienteCiudadano.objects.create(
        expediente=expediente,
        ciudadano=c1,
        estado=estado_legajo,
        revision_tecnico=RevisionTecnico.SUBSANAR,
    )
    ExpedienteCiudadano.objects.create(
        expediente=expediente,
        ciudadano=c2,
        estado=estado_legajo,
        revision_tecnico=RevisionTecnico.PENDIENTE,
    )

    client.force_login(admin)

    # Sin filtro
    response_sin = client.get(reverse("expediente_list"))
    exp_sin = next(e for e in response_sin.context["expedientes"] if e.pk == expediente.pk)
    count_sin_filtro = exp_sin.legajos_subsanar_count

    # Con filtro por nombre de provincia (fuerza JOIN sobre expediente_ciudadanos)
    response_con = client.get(reverse("expediente_list"), {"q": provincia.nombre})
    exp_con = next(e for e in response_con.context["expedientes"] if e.pk == expediente.pk)
    count_con_filtro = exp_con.legajos_subsanar_count

    assert count_sin_filtro == 1
    assert count_con_filtro == 1
