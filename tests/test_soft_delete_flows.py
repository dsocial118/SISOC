import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from comedores.models import (
    Comedor,
    EstadoActividad,
    EstadoGeneral,
    EstadoHistorial,
    EstadoProceso,
)
from centrodefamilia.models import Actividad, Categoria
from core.soft_delete_preview import build_delete_preview


@pytest.mark.django_db
def test_soft_delete_single_model_and_restore():
    user = get_user_model().objects.create_user(
        username="soft_user",
        password="x",
    )
    categoria = Categoria.objects.create(nombre="Categoria SD")

    deleted_count, _ = categoria.delete(user=user, cascade=True)
    assert deleted_count == 1
    assert not Categoria.objects.filter(pk=categoria.pk).exists()

    deleted = Categoria.all_objects.get(pk=categoria.pk)
    assert deleted.deleted_at is not None
    assert deleted.deleted_by_id == user.id

    restored_count, _ = deleted.restore(user=user, cascade=True)
    assert restored_count == 1
    assert Categoria.objects.filter(pk=categoria.pk).exists()


@pytest.mark.django_db
def test_soft_delete_cascade_and_restore_cascade():
    user = get_user_model().objects.create_user(
        username="cascade_user",
        password="x",
    )
    categoria = Categoria.objects.create(nombre="Cat Cascada")
    actividad = Actividad.objects.create(nombre="Act Cascada", categoria=categoria)

    preview = build_delete_preview(categoria)
    assert preview["total_afectados"] == 2

    categoria.delete(user=user, cascade=True)
    assert not Categoria.objects.filter(pk=categoria.pk).exists()
    assert not Actividad.objects.filter(pk=actividad.pk).exists()

    categoria_deleted = Categoria.all_objects.get(pk=categoria.pk)
    categoria_deleted.restore(user=user, cascade=True)
    assert Categoria.objects.filter(pk=categoria.pk).exists()
    assert Actividad.objects.filter(pk=actividad.pk).exists()


@pytest.mark.django_db
def test_papelera_only_superadmin_can_access(client):
    normal_user = get_user_model().objects.create_user(
        username="normal_user",
        password="x",
    )
    superuser = get_user_model().objects.create_superuser(
        username="super_user",
        email="super@example.com",
        password="x",
    )

    client.force_login(normal_user)
    resp_forbidden = client.get(reverse("papelera_list"))
    assert resp_forbidden.status_code == 403

    client.force_login(superuser)
    resp_ok = client.get(reverse("papelera_list"))
    assert resp_ok.status_code == 200


@pytest.mark.django_db
def test_soft_delete_comedor_with_protected_ultimo_estado():
    user = get_user_model().objects.create_user(
        username="comedor_user",
        password="x",
    )
    estado_actividad = EstadoActividad.objects.create(estado="Activo")
    estado_proceso = EstadoProceso.objects.create(
        estado="En ejecución",
        estado_actividad=estado_actividad,
    )
    estado_general = EstadoGeneral.objects.create(
        estado_actividad=estado_actividad,
        estado_proceso=estado_proceso,
    )
    comedor = Comedor.objects.create(nombre="Comedor soft delete")
    historial = EstadoHistorial.objects.create(
        comedor=comedor,
        estado_general=estado_general,
        usuario=user,
    )
    comedor.ultimo_estado = historial
    comedor.save(update_fields=["ultimo_estado"])

    preview = build_delete_preview(comedor)
    assert preview["total_afectados"] == 1

    deleted_count, _ = comedor.delete(user=user, cascade=True)
    assert deleted_count == 1
    assert Comedor.objects.filter(pk=comedor.pk).exists() is False

    comedor_deleted = Comedor.all_objects.get(pk=comedor.pk)
    assert comedor_deleted.deleted_at is not None
    assert EstadoHistorial.objects.filter(pk=historial.pk).exists()
