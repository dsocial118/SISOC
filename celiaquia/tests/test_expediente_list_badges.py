"""Colores de los badges de estado en el listado de expedientes (tk #2319)."""

from datetime import date

import pytest
from django.contrib.auth.models import Permission, User
from django.urls import reverse

from ciudadanos.models import Ciudadano
from core.models import Provincia
from celiaquia.models import (
    EstadoExpediente,
    EstadoLegajo,
    Expediente,
    ExpedienteCiudadano,
    RevisionTecnico,
)
from users.models import Profile


def _usuario_provincial(provincia):
    user = User.objects.create_user(username="prov", password="pass")
    user.user_permissions.add(
        Permission.objects.get(
            content_type__app_label="celiaquia",
            codename="view_expediente",
        )
    )
    profile, _ = Profile.objects.get_or_create(user=user)
    profile.es_usuario_provincial = True
    profile.provincia = provincia
    profile.save()
    return user


def _legajo(expediente, provincia, documento, revision):
    ciudadano = Ciudadano.objects.create(
        apellido="Perez",
        nombre=f"Ciudadano {documento}",
        fecha_nacimiento=date(2010, 1, 1),
        documento=documento,
        provincia=provincia,
    )
    estado_legajo, _ = EstadoLegajo.objects.get_or_create(nombre="DOCUMENTO_PENDIENTE")
    return ExpedienteCiudadano.objects.create(
        expediente=expediente,
        ciudadano=ciudadano,
        estado=estado_legajo,
        revision_tecnico=revision,
    )


@pytest.mark.django_db
def test_subsanados_no_usa_el_verde_de_cruce_finalizado(client):
    """Subsanado y Cruce finalizado se muestran en la misma celda del listado:
    si ambos fueran verdes no se distinguirían."""
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    estado = EstadoExpediente.objects.create(nombre="CRUCE_FINALIZADO")
    user = _usuario_provincial(provincia)
    expediente = Expediente.objects.create(usuario_provincia=user, estado=estado)
    _legajo(expediente, provincia, "60000001", RevisionTecnico.SUBSANADO)

    client.force_login(user)
    html = client.get(reverse("expediente_list")).content.decode()

    assert "badge badge-subsanado" in html
    assert "1 subsanados" in html
    # El verde queda reservado al estado del expediente.
    assert 'class="badge bg-success"' not in html


@pytest.mark.django_db
def test_a_subsanar_conserva_el_amarillo(client):
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    estado = EstadoExpediente.objects.create(nombre="EN_ESPERA")
    user = _usuario_provincial(provincia)
    expediente = Expediente.objects.create(usuario_provincia=user, estado=estado)
    _legajo(expediente, provincia, "60000002", RevisionTecnico.SUBSANAR)

    client.force_login(user)
    html = client.get(reverse("expediente_list")).content.decode()

    assert "badge bg-warning text-dark" in html
    assert "1 a subsanar" in html
