"""Fase 1: solicitud de subsanación con múltiples motivos y observaciones.

Verifica que al solicitar una subsanación (Nación) se cree un objeto Subsanacion
con una observación por cada motivo/observación, preservando los campos legacy
del legajo para compatibilidad.
"""

from datetime import date

import pytest
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from ciudadanos.models import Ciudadano
from celiaquia.models import (
    EstadoExpediente,
    EstadoLegajo,
    Expediente,
    ExpedienteCiudadano,
    RevisionTecnico,
)


def _grant(user, app_label, codename, model=User, name=None):
    content_type = ContentType.objects.get_for_model(model)
    perm, _ = Permission.objects.get_or_create(
        codename=codename,
        content_type=content_type,
        defaults={"name": name or codename},
    )
    user.user_permissions.add(perm)


def _coordinador():
    user = User.objects.create_user(username="coord-subs", password="pass")
    _grant(user, "celiaquia", "view_expediente", model=Expediente)
    _grant(user, "auth", "role_coordinadorceliaquia", name="Coordinador Celiaquia")
    return user


def _legajo(estado_legajo, expediente, doc=88001):
    ciudadano = Ciudadano.objects.create(
        apellido="Test",
        nombre="Subsanar",
        documento=doc,
        fecha_nacimiento=date(1990, 1, 1),
    )
    return ExpedienteCiudadano.objects.create(
        expediente=expediente,
        ciudadano=ciudadano,
        estado=estado_legajo,
        revision_tecnico=RevisionTecnico.PENDIENTE,
    )


@pytest.mark.django_db
def test_solicitud_subsanacion_crea_observaciones_multiples(client):
    user = _coordinador()
    estado_exp = EstadoExpediente.objects.create(nombre="ASIGNADO")
    estado_legajo = EstadoLegajo.objects.create(nombre="DOCUMENTO_PENDIENTE")
    expediente = Expediente.objects.create(usuario_provincia=user, estado=estado_exp)
    legajo = _legajo(estado_legajo, expediente)

    client.force_login(user)
    response = client.post(
        reverse("legajo_revisar", args=[expediente.pk, legajo.pk]),
        data={
            "accion": "SUBSANAR",
            "motivos": ["DOCUMENTACION", "DATOS_PERSONALES"],
            "motivo": "Revisar documentación y datos",
            "observacion_tipo": ["DOCUMENTACION"],
            "observacion_detalle": ["Adjuntar nuevamente DNI frente"],
        },
    )

    assert response.status_code == 200
    assert response.json().get("success") is True

    legajo.refresh_from_db()
    assert legajo.revision_tecnico == RevisionTecnico.SUBSANAR
    # Campos legacy preservados.
    assert legajo.subsanacion_motivo == "Revisar documentación y datos"
    assert legajo.subsanacion_tipo in {"DOCUMENTACION", "DATOS_PERSONALES"}

    # Una subsanación con dos observaciones: la específica (DOCUMENTACION con su
    # detalle) y la del motivo DATOS_PERSONALES (con el detalle general).
    subsanaciones = list(legajo.subsanaciones.all())
    assert len(subsanaciones) == 1
    subsanacion = subsanaciones[0]
    assert subsanacion.estado == "PENDIENTE"
    assert subsanacion.solicitada_por_id == user.id

    observaciones = {
        obs.tipo: (obs.detalle or "") for obs in subsanacion.observaciones.all()
    }
    assert observaciones == {
        "DOCUMENTACION": "Adjuntar nuevamente DNI frente",
        "DATOS_PERSONALES": "Revisar documentación y datos",
    }
    assert set(subsanacion.tipos) == {"DOCUMENTACION", "DATOS_PERSONALES"}


@pytest.mark.django_db
def test_solicitud_subsanacion_legacy_un_solo_tipo(client):
    """Compatibilidad: si solo llega tipo_subsanacion (formato viejo) se crea una
    única observación."""
    user = _coordinador()
    estado_exp = EstadoExpediente.objects.create(nombre="ASIGNADO")
    estado_legajo = EstadoLegajo.objects.create(nombre="DOCUMENTO_PENDIENTE")
    expediente = Expediente.objects.create(usuario_provincia=user, estado=estado_exp)
    legajo = _legajo(estado_legajo, expediente, doc=88002)

    client.force_login(user)
    response = client.post(
        reverse("legajo_revisar", args=[expediente.pk, legajo.pk]),
        data={
            "accion": "SUBSANAR",
            "tipo_subsanacion": "RENAPER",
            "motivo": "Validar identidad",
        },
    )

    assert response.status_code == 200
    legajo.refresh_from_db()
    subsanacion = legajo.subsanaciones.get()
    observaciones = list(subsanacion.observaciones.all())
    assert len(observaciones) == 1
    assert observaciones[0].tipo == "RENAPER"
    assert observaciones[0].detalle == "Validar identidad"
