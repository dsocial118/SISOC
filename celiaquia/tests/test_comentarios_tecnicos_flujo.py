"""Endpoints de comentarios técnicos del legajo (issue #2318).

Cubre el alta estructurada, el listado según quién consulta y la
previsualización del motivo que arma el backend.
"""

from datetime import date

import pytest
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from ciudadanos.models import Ciudadano
from core.models import Provincia
from users.models import Profile, ProfileTerritorialScope
from celiaquia.models import (
    EstadoExpediente,
    EstadoLegajo,
    Expediente,
    ExpedienteCiudadano,
    HistorialComentarios,
    RevisionTecnico,
)
from celiaquia.services.comentarios_tecnicos_service import ComentariosTecnicosService

pytestmark = pytest.mark.django_db

CODIGO_RENAPER = "RENAPER_FECHA_NACIMIENTO"
CODIGO_DIAG = "DIAG_DOC_ILEGIBLE"


def _grant(user, codename, model=User, name=None):
    content_type = ContentType.objects.get_for_model(model)
    perm, _ = Permission.objects.get_or_create(
        codename=codename,
        content_type=content_type,
        defaults={"name": name or codename},
    )
    user.user_permissions.add(perm)


@pytest.fixture(name="coordinador")
def fixture_coordinador():
    user = User.objects.create_user(username="coord-ct", password="pass")
    _grant(user, "view_expediente", model=Expediente)
    _grant(user, "role_coordinadorceliaquia", name="Coordinador Celiaquia")
    return user


@pytest.fixture(name="provincia_obj")
def fixture_provincia():
    return Provincia.objects.create(nombre="Prov CT")


@pytest.fixture(name="provincial")
def fixture_provincial(provincia_obj):
    user = User.objects.create_user(username="prov-ct", password="pass")
    _grant(user, "view_expediente", model=Expediente)
    _grant(user, "role_provinciaceliaquia", name="Provincia Celiaquia")
    profile, _ = Profile.objects.get_or_create(user=user)
    profile.es_usuario_provincial = True
    profile.save()
    ProfileTerritorialScope.objects.create(profile=profile, provincia=provincia_obj)
    return user


@pytest.fixture(name="legajo")
def fixture_legajo(coordinador, provincia_obj):
    estado_exp = EstadoExpediente.objects.create(nombre="ASIGNADO")
    estado_legajo = EstadoLegajo.objects.create(nombre="DOCUMENTO_PENDIENTE")
    expediente = Expediente.objects.create(
        usuario_provincia=coordinador, estado=estado_exp
    )
    ciudadano = Ciudadano.objects.create(
        apellido="Flujo",
        nombre="Comentario",
        documento="77000111",
        fecha_nacimiento=date(1990, 1, 1),
        provincia=provincia_obj,
    )
    return ExpedienteCiudadano.objects.create(
        expediente=expediente,
        ciudadano=ciudadano,
        estado=estado_legajo,
        revision_tecnico=RevisionTecnico.PENDIENTE,
    )


def _url_crear(legajo):
    return reverse("legajo_comentario_create", args=[legajo.expediente_id, legajo.pk])


def _url_listar(legajo):
    return reverse("legajo_comentarios_list", args=[legajo.expediente_id, legajo.pk])


def _url_preview(legajo):
    return reverse("legajo_motivo_preview", args=[legajo.expediente_id, legajo.pk])


def _sembrar(legajo, usuario, con_si=True, con_no=True):
    if con_si:
        ComentariosTecnicosService.registrar(
            legajo,
            tipo_documento="RENAPER",
            tiene_observaciones=True,
            observacion_codigo=CODIGO_RENAPER,
            usuario=usuario,
        )
        ComentariosTecnicosService.registrar(
            legajo,
            tipo_documento="CONDICION_DIAGNOSTICA",
            tiene_observaciones=True,
            observacion_codigo=CODIGO_DIAG,
            usuario=usuario,
        )
    if con_no:
        ComentariosTecnicosService.registrar(
            legajo,
            tipo_documento="ANSES",
            tiene_observaciones=False,
            usuario=usuario,
        )


# --- Fase 3: endpoints ----------------------------------------------------


def test_alta_estructurada_por_endpoint(client, coordinador, legajo):
    client.force_login(coordinador)

    response = client.post(
        _url_crear(legajo),
        data={
            "tipo_documento": "RENAPER",
            "tiene_observaciones": "si",
            "observacion_codigo": CODIGO_RENAPER,
        },
    )

    assert response.status_code == 200
    payload = response.json()["comentario"]
    assert payload["es_comentario_tecnico"] is True
    assert payload["tipo_documento"] == "RENAPER"
    assert payload["tiene_observaciones"] is True
    assert payload["es_interno"] is True

    comentario = HistorialComentarios.objects.get(pk=payload["id"])
    assert comentario.tipo_comentario == HistorialComentarios.TIPO_COMENTARIO_TECNICO


def test_alta_estructurada_invalida_devuelve_400(client, coordinador, legajo):
    client.force_login(coordinador)

    response = client.post(
        _url_crear(legajo),
        data={
            "tipo_documento": "ANSES",
            "tiene_observaciones": "si",
            "observacion_codigo": CODIGO_RENAPER,  # código de otro tipo
        },
    )

    assert response.status_code == 400
    assert not ComentariosTecnicosService.historial(legajo).exists()


def test_alta_libre_sigue_funcionando(client, coordinador, legajo):
    """El formato previo al issue #2318 no se rompe."""
    client.force_login(coordinador)

    response = client.post(
        _url_crear(legajo), data={"comentario": "Observación suelta", "es_interno": "1"}
    )

    assert response.status_code == 200
    comentario = HistorialComentarios.objects.get(
        pk=response.json()["comentario"]["id"]
    )
    assert comentario.tipo_comentario == HistorialComentarios.TIPO_OBSERVACION_GENERAL
    assert comentario.es_comentario_tecnico is False


def test_listado_nacion_ve_los_internos(client, coordinador, legajo):
    _sembrar(legajo, coordinador)
    client.force_login(coordinador)

    comentarios = client.get(_url_listar(legajo)).json()["comentarios"]

    tecnicos = [c for c in comentarios if c["es_comentario_tecnico"]]
    assert len(tecnicos) == 3
    assert all(c["es_interno"] for c in tecnicos)


def test_listado_provincia_no_ve_comentarios_sin_publicar(
    client, coordinador, provincial, legajo
):
    _sembrar(legajo, coordinador)
    client.force_login(provincial)

    assert client.get(_url_listar(legajo)).json()["comentarios"] == []


def test_listado_provincia_deduplica_las_observaciones_publicadas(
    client, coordinador, provincial, legajo
):
    _sembrar(legajo, coordinador, con_no=False)
    # Misma observación registrada dos veces: el historial la conserva, la
    # Provincia la ve una sola vez.
    ComentariosTecnicosService.registrar(
        legajo,
        tipo_documento="RENAPER",
        tiene_observaciones=True,
        observacion_codigo=CODIGO_RENAPER,
        usuario=coordinador,
    )
    ComentariosTecnicosService.publicar(legajo, usuario=coordinador)

    client.force_login(coordinador)
    assert len(client.get(_url_listar(legajo)).json()["comentarios"]) == 3

    client.force_login(provincial)
    assert len(client.get(_url_listar(legajo)).json()["comentarios"]) == 2


def test_preview_devuelve_las_lineas_concatenadas(client, coordinador, legajo):
    _sembrar(legajo, coordinador)
    client.force_login(coordinador)

    payload = client.get(_url_preview(legajo)).json()

    assert payload["tiene_observaciones"] is True
    assert len(payload["lineas"]) == 2
    assert payload["lineas"][0].startswith("RENAPER: ")
    assert "Sin observaciones." not in payload["motivo"]


def test_preview_sin_observaciones(client, coordinador, legajo):
    _sembrar(legajo, coordinador, con_si=False)
    client.force_login(coordinador)

    payload = client.get(_url_preview(legajo)).json()

    assert payload["tiene_observaciones"] is False
    assert payload["motivo"] == ""


def test_preview_denegado_para_provincia(client, provincial, legajo):
    client.force_login(provincial)

    assert client.get(_url_preview(legajo)).status_code == 403
