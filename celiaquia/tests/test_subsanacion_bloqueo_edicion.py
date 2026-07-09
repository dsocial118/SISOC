"""Fase 3: bloqueo de edición/reemplazo de documentos observados.

Una vez que el legajo está en subsanación (o el expediente fue enviado), los
documentos originales no pueden reemplazarse por el endpoint de carga: las
correcciones se cargan como archivos de subsanación.
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
    SubsanacionEstado,
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


def _setup(username, doc, estado_exp_nombre, revision):
    provincia = Provincia.objects.create(nombre=f"{username} Prov")
    municipio = Municipio.objects.create(nombre=f"{username} Mun", provincia=provincia)
    localidad = Localidad.objects.create(nombre=f"{username} Loc", municipio=municipio)
    user = _provincial_user(username, provincia)
    estado_exp = EstadoExpediente.objects.create(nombre=estado_exp_nombre)
    estado_legajo = EstadoLegajo.objects.create(nombre=f"EST_{username}")
    expediente = Expediente.objects.create(usuario_provincia=user, estado=estado_exp)
    ciudadano = Ciudadano.objects.create(
        apellido="Test",
        nombre="Bloqueo",
        documento=doc,
        fecha_nacimiento=date(1990, 1, 1),
        provincia=provincia,
        municipio=municipio,
        localidad=localidad,
    )
    legajo = ExpedienteCiudadano.objects.create(
        expediente=expediente,
        ciudadano=ciudadano,
        estado=estado_legajo,
        revision_tecnico=revision,
    )
    return user, expediente, legajo


@pytest.mark.django_db
def test_no_se_puede_reemplazar_documento_en_subsanacion(client):
    user, expediente, legajo = _setup(
        "prov-bloq-subs", 95001, "EN_ESPERA", RevisionTecnico.SUBSANAR
    )
    Subsanacion.objects.create(
        legajo=legajo,
        estado=SubsanacionEstado.PENDIENTE,
        solicitada_por=user,
    )

    client.force_login(user)
    response = client.post(
        reverse("legajo_archivo_upload", args=[expediente.pk, legajo.pk]),
        data={"slot": "2", "archivo": SimpleUploadedFile("nuevo.pdf", b"data")},
    )

    assert response.status_code == 409
    assert response.json().get("success") is False
    legajo.refresh_from_db()
    # No se cargó el archivo original.
    assert not legajo.archivo2


@pytest.mark.django_db
def test_se_puede_cargar_documento_inicial_en_espera(client):
    """En EN_ESPERA, sin subsanación y sin observación, la carga inicial sigue
    permitida (no rompe el flujo normal)."""
    user, expediente, legajo = _setup(
        "prov-carga-ok", 95002, "EN_ESPERA", RevisionTecnico.PENDIENTE
    )

    client.force_login(user)
    response = client.post(
        reverse("legajo_archivo_upload", args=[expediente.pk, legajo.pk]),
        data={"slot": "2", "archivo": SimpleUploadedFile("inicial.pdf", b"data")},
    )

    assert response.status_code == 200
    assert response.json().get("success") is True
    legajo.refresh_from_db()
    assert bool(legajo.archivo2) is True
