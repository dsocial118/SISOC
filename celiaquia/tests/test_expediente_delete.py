"""Tests de regresión para eliminación de expedientes en Celiaquía."""

import json

import pytest
from django.contrib.auth.models import User
from django.test import RequestFactory

from celiaquia.models import EstadoExpediente, Expediente
from celiaquia.views.expediente import ExpedienteDeleteView


pytestmark = pytest.mark.django_db
factory = RequestFactory()


def _crear_expediente():
    usuario_provincia = User.objects.create_user(
        username=f"prov_delete_{User.objects.count() + 1}",
        password="testpass123",
    )
    estado = EstadoExpediente.objects.create(
        nombre=f"CREADO_DELETE_{EstadoExpediente.objects.count() + 1}"
    )
    return Expediente.objects.create(usuario_provincia=usuario_provincia, estado=estado)


def test_superusuario_puede_eliminar_expediente_con_soft_delete():
    superuser = User.objects.create_superuser(
        username="admin_delete",
        email="admin_delete@example.com",
        password="testpass123",
    )
    expediente = _crear_expediente()
    request = factory.delete(f"/celiaquia/expedientes/{expediente.pk}/eliminar/")
    request.user = superuser

    response = ExpedienteDeleteView.as_view()(request, pk=expediente.pk)

    assert response.status_code == 200
    assert json.loads(response.content)["success"] is True
    assert not Expediente.objects.filter(pk=expediente.pk).exists()
    expediente_eliminado = Expediente.all_objects.get(pk=expediente.pk)
    assert expediente_eliminado.deleted_at is not None
    assert expediente_eliminado.deleted_by_id == superuser.id


def test_usuario_no_superuser_recibe_403_al_eliminar_expediente():
    usuario = User.objects.create_user(
        username="usuario_no_admin",
        password="testpass123",
    )
    expediente = _crear_expediente()
    request = factory.delete(f"/celiaquia/expedientes/{expediente.pk}/eliminar/")
    request.user = usuario

    response = ExpedienteDeleteView.as_view()(request, pk=expediente.pk)

    assert response.status_code == 403
    assert json.loads(response.content)["success"] is False
    assert Expediente.objects.filter(pk=expediente.pk).exists()


def test_eliminar_expediente_inexistente_es_idempotente():
    superuser = User.objects.create_superuser(
        username="admin_delete_idempotente",
        email="admin_delete_idempotente@example.com",
        password="testpass123",
    )
    request = factory.delete("/celiaquia/expedientes/999999/eliminar/")
    request.user = superuser

    response = ExpedienteDeleteView.as_view()(request, pk=999999)

    assert response.status_code == 200
    payload = json.loads(response.content)
    assert payload["success"] is True
    assert payload["already_deleted"] is True
