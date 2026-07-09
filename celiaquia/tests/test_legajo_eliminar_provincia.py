"""Tests: eliminación de legajos por usuarios provinciales antes del envío.

Criterios cubiertos:
- La provincia puede eliminar un legajo mientras el expediente está pendiente de
  envío (estado EN_ESPERA).
- Una vez enviado (CONFIRMACION_DE_ENVIO) la provincia no puede eliminar.
- Las acciones de revisión (APROBAR/RECHAZAR/SUBSANAR) siguen vedadas a la
  provincia.
- Al eliminar el legajo se da de baja en cascada (deja de estar visible).
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
)


def _grant(user, app_label, codename, model=User, name=None):
    content_type = ContentType.objects.get_for_model(model)
    perm, _ = Permission.objects.get_or_create(
        codename=codename,
        content_type=content_type,
        defaults={"name": name or codename},
    )
    user.user_permissions.add(perm)


def _provincial_user(username, provincia):
    user = User.objects.create_user(username=username, password="pass")
    _grant(user, "celiaquia", "view_expediente", model=Expediente)
    _grant(
        user,
        "auth",
        "role_provinciaceliaquia",
        name="Permiso provincia Celiaquia",
    )
    profile, _ = Profile.objects.get_or_create(user=user)
    profile.es_usuario_provincial = True
    profile.save()
    ProfileTerritorialScope.objects.create(profile=profile, provincia=provincia)
    return user


def _territorio(nombre):
    provincia = Provincia.objects.create(nombre=f"{nombre} Prov")
    municipio = Municipio.objects.create(nombre=f"{nombre} Mun", provincia=provincia)
    localidad = Localidad.objects.create(nombre=f"{nombre} Loc", municipio=municipio)
    return provincia, municipio, localidad


def _expediente_con_legajo(owner, estado, provincia, municipio, localidad, doc=7001):
    expediente = Expediente.objects.create(usuario_provincia=owner, estado=estado)
    ciudadano = Ciudadano.objects.create(
        apellido="Perez",
        nombre=f"Ciudadano {doc}",
        fecha_nacimiento=date(2010, 1, 1),
        documento=doc,
        provincia=provincia,
        municipio=municipio,
        localidad=localidad,
    )
    estado_legajo, _ = EstadoLegajo.objects.get_or_create(nombre="DOCUMENTO_PENDIENTE")
    legajo = ExpedienteCiudadano.objects.create(
        expediente=expediente, ciudadano=ciudadano, estado=estado_legajo
    )
    return expediente, legajo


@pytest.mark.django_db
def test_provincia_puede_eliminar_legajo_antes_del_envio(client):
    provincia, municipio, localidad = _territorio("BsAs Del")
    user = _provincial_user("prov-del-ok", provincia)
    estado = EstadoExpediente.objects.create(nombre="EN_ESPERA")
    expediente, legajo = _expediente_con_legajo(
        user, estado, provincia, municipio, localidad
    )

    client.force_login(user)
    response = client.post(
        reverse("legajo_revisar", args=[expediente.pk, legajo.pk]),
        data={"accion": "ELIMINAR"},
    )

    assert response.status_code == 200
    assert response.json().get("success") is True
    # El legajo queda dado de baja (no visible en el manager por defecto).
    assert not ExpedienteCiudadano.objects.filter(pk=legajo.pk).exists()


@pytest.mark.django_db
def test_provincia_no_puede_eliminar_legajo_luego_del_envio(client):
    provincia, municipio, localidad = _territorio("BsAs Enviado")
    user = _provincial_user("prov-del-enviado", provincia)
    estado = EstadoExpediente.objects.create(nombre="CONFIRMACION_DE_ENVIO")
    expediente, legajo = _expediente_con_legajo(
        user, estado, provincia, municipio, localidad, doc=7002
    )

    client.force_login(user)
    response = client.post(
        reverse("legajo_revisar", args=[expediente.pk, legajo.pk]),
        data={"accion": "ELIMINAR"},
    )

    assert response.status_code == 403
    assert response.json().get("success") is False
    # El legajo sigue existiendo.
    assert ExpedienteCiudadano.objects.filter(pk=legajo.pk).exists()


@pytest.mark.django_db
def test_provincia_no_puede_revisar_legajo(client):
    provincia, municipio, localidad = _territorio("BsAs Revision")
    user = _provincial_user("prov-del-revision", provincia)
    estado = EstadoExpediente.objects.create(nombre="EN_ESPERA")
    expediente, legajo = _expediente_con_legajo(
        user, estado, provincia, municipio, localidad, doc=7003
    )

    client.force_login(user)
    response = client.post(
        reverse("legajo_revisar", args=[expediente.pk, legajo.pk]),
        data={"accion": "APROBAR"},
    )

    assert response.status_code == 403
    assert ExpedienteCiudadano.objects.filter(pk=legajo.pk).exists()
