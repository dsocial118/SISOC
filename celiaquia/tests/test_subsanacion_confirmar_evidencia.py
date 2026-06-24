"""Deuda técnica: confirmar la subsanación (→ SUBSANADO) exige evidencia nueva.

No basta con que existan los archivos originales: la provincia debe haber
cargado al menos un archivo de subsanación (SubsanacionArchivo) antes de poder
confirmar.
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


def _setup(username, doc):
    provincia = Provincia.objects.create(nombre=f"{username} Prov")
    municipio = Municipio.objects.create(nombre=f"{username} Mun", provincia=provincia)
    localidad = Localidad.objects.create(nombre=f"{username} Loc", municipio=municipio)
    user = _provincial_user(username, provincia)
    estado_exp = EstadoExpediente.objects.create(nombre="EN_ESPERA")
    estado_legajo = EstadoLegajo.objects.create(nombre=f"EST_{username}")
    expediente = Expediente.objects.create(usuario_provincia=user, estado=estado_exp)
    ciudadano = Ciudadano.objects.create(
        apellido="Test",
        nombre="Confirmar",
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
        revision_tecnico=RevisionTecnico.SUBSANAR,
        archivo2=SimpleUploadedFile("orig2.pdf", b"o2"),
        archivo3=SimpleUploadedFile("orig3.pdf", b"o3"),
    )
    subsanacion = Subsanacion.objects.create(
        legajo=legajo,
        estado=SubsanacionEstado.PENDIENTE,
        solicitada_por=user,
    )
    return user, expediente, legajo, subsanacion


@pytest.mark.django_db
def test_confirmar_sin_evidencia_falla(client):
    user, expediente, legajo, _sub = _setup("prov-conf-sin", 96001)

    client.force_login(user)
    response = client.post(
        reverse("expediente_confirm_subsanacion", args=[expediente.pk]),
        data={"legajo_id": legajo.pk},
    )

    assert response.status_code == 400
    legajo.refresh_from_db()
    assert legajo.revision_tecnico == RevisionTecnico.SUBSANAR


@pytest.mark.django_db
def test_confirmar_con_evidencia_pasa_a_subsanado(client):
    user, expediente, legajo, subsanacion = _setup("prov-conf-ok", 96002)
    SubsanacionArchivo.objects.create(
        subsanacion=subsanacion,
        archivo=SimpleUploadedFile("corregido.pdf", b"nuevo"),
        usuario=user,
    )

    client.force_login(user)
    response = client.post(
        reverse("expediente_confirm_subsanacion", args=[expediente.pk]),
        data={"legajo_id": legajo.pk},
    )

    assert response.status_code == 200
    assert response.json().get("success") is True
    legajo.refresh_from_db()
    assert legajo.revision_tecnico == RevisionTecnico.SUBSANADO


@pytest.mark.django_db
def test_confirmacion_masiva_ignora_subsanaciones_renaper(client):
    """La confirmación masiva confirma las subsanaciones técnicas con evidencia y
    NO se traba por legajos de subsanación RENAPER (que se resuelven aparte)."""
    admin = User.objects.create_superuser(username="admin-masiva", password="pass")
    estado_exp = EstadoExpediente.objects.create(nombre="EST_MASIVA")
    estado_legajo = EstadoLegajo.objects.create(nombre="EST_LEG_MASIVA")
    expediente = Expediente.objects.create(usuario_provincia=admin, estado=estado_exp)

    # Legajo técnico: archivos originales + evidencia de subsanación.
    ciud_tec = Ciudadano.objects.create(
        apellido="Tec",
        nombre="Conalt",
        documento=97001,
        fecha_nacimiento=date(1990, 1, 1),
    )
    legajo_tec = ExpedienteCiudadano.objects.create(
        expediente=expediente,
        ciudadano=ciud_tec,
        estado=estado_legajo,
        revision_tecnico=RevisionTecnico.SUBSANAR,
        archivo2=SimpleUploadedFile("o2.pdf", b"o2"),
        archivo3=SimpleUploadedFile("o3.pdf", b"o3"),
    )
    sub = Subsanacion.objects.create(
        legajo=legajo_tec, estado=SubsanacionEstado.PENDIENTE, solicitada_por=admin
    )
    SubsanacionArchivo.objects.create(
        subsanacion=sub,
        archivo=SimpleUploadedFile("corregido.pdf", b"x"),
        usuario=admin,
    )

    # Legajo RENAPER (estado_validacion_renaper=3, sin Subsanacion ni evidencia).
    ciud_ren = Ciudadano.objects.create(
        apellido="Ren",
        nombre="Aper",
        documento=97002,
        fecha_nacimiento=date(1990, 1, 1),
    )
    legajo_ren = ExpedienteCiudadano.objects.create(
        expediente=expediente,
        ciudadano=ciud_ren,
        estado=estado_legajo,
        revision_tecnico=RevisionTecnico.SUBSANAR,
        estado_validacion_renaper=3,
    )

    client.force_login(admin)
    response = client.post(
        reverse("expediente_confirm_subsanacion", args=[expediente.pk]),
        data={},
    )

    assert response.status_code == 200
    legajo_tec.refresh_from_db()
    legajo_ren.refresh_from_db()
    # El técnico se confirma; el RENAPER no se toca (lo resuelve su propio flujo).
    assert legajo_tec.revision_tecnico == RevisionTecnico.SUBSANADO
    assert legajo_ren.revision_tecnico == RevisionTecnico.SUBSANAR
