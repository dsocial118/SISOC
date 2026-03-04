from datetime import datetime

import pytest
from django.contrib.auth import get_user_model
from django.db.utils import OperationalError
from django.urls import reverse
from django.utils import timezone

from comedores.models import (
    Comedor,
    EstadoActividad,
    EstadoGeneral,
    EstadoHistorial,
    EstadoProceso,
)
from centrodefamilia.models import Actividad, Categoria
from core.soft_delete.preview import build_delete_preview


def _categoria_model_key():
    return f"{Categoria._meta.app_label}.{Categoria.__name__}"


def _set_deleted_at(instance, value):
    instance.__class__.all_objects.filter(pk=instance.pk).update(deleted_at=value)
    instance.deleted_at = value


def _create_deleted_categoria(nombre, deleted_by):
    categoria = Categoria.objects.create(nombre=nombre)
    categoria.delete(user=deleted_by, cascade=True)
    return Categoria.all_objects.get(pk=categoria.pk)


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
def test_papelera_list_filters_by_deleted_by(auth_client):
    user_model = get_user_model()
    deleter_1 = user_model.objects.create_user(username="maria.papelera", password="x")
    deleter_2 = user_model.objects.create_user(username="juan.papelera", password="x")

    kept = _create_deleted_categoria("Categoria Maria", deleter_1)
    hidden = _create_deleted_categoria("Categoria Juan", deleter_2)

    response = auth_client.get(
        reverse("papelera_list"),
        {"model": _categoria_model_key(), "deleted_by": "maria"},
    )

    assert response.status_code == 200
    content = response.content.decode()
    assert str(kept) in content
    assert str(hidden) not in content
    assert "Filtros activos:" in content


@pytest.mark.django_db
def test_papelera_list_filters_by_deleted_date_range(auth_client):
    user_model = get_user_model()
    deleter = user_model.objects.create_user(username="date_filter_user", password="x")

    inside = _create_deleted_categoria("Categoria Dentro Rango", deleter)
    outside = _create_deleted_categoria("Categoria Fuera Rango", deleter)

    inside_dt = timezone.make_aware(datetime(2026, 1, 10, 10, 30, 0))
    outside_dt = timezone.make_aware(datetime(2026, 2, 20, 9, 0, 0))
    _set_deleted_at(inside, inside_dt)
    _set_deleted_at(outside, outside_dt)

    response = auth_client.get(
        reverse("papelera_list"),
        {
            "model": _categoria_model_key(),
            "deleted_from": "2026-01-01",
            "deleted_to": "2026-01-31",
        },
    )

    assert response.status_code == 200
    content = response.content.decode()
    assert str(inside) in content
    assert str(outside) not in content


@pytest.mark.django_db
def test_papelera_list_invalid_date_range_shows_error(auth_client):
    response = auth_client.get(
        reverse("papelera_list"),
        {
            "model": _categoria_model_key(),
            "deleted_from": "2026-02-10",
            "deleted_to": "2026-02-01",
        },
    )

    assert response.status_code == 200
    content = response.content.decode()
    assert (
        "La fecha &#x27;Desde&#x27; no puede ser posterior a la fecha &#x27;Hasta&#x27;."
        in content
    )
    assert "alert alert-warning" in content


@pytest.mark.django_db
def test_papelera_list_fallbacks_when_queryset_count_fails(auth_client, monkeypatch):
    user_model = get_user_model()
    deleter = user_model.objects.create_user(username="count_fail_user", password="x")
    deleted = _create_deleted_categoria("Categoria Count Fail", deleter)

    failing_queryset = Categoria.all_objects.filter(
        pk=deleted.pk,
        deleted_at__isnull=False,
    ).order_by("-deleted_at", "-pk")

    def _raise_count_error():
        raise OperationalError(
            1222,
            "The used SELECT statements have a different number of columns",
        )

    monkeypatch.setattr(failing_queryset, "count", _raise_count_error)
    monkeypatch.setattr(
        "core.trash_views._build_deleted_queryset",
        lambda **kwargs: failing_queryset,
    )

    response = auth_client.get(
        reverse("papelera_list"), {"model": _categoria_model_key()}
    )

    assert response.status_code == 200
    assert str(deleted) in response.content.decode()


@pytest.mark.django_db
def test_papelera_pagination_preserves_filters(auth_client):
    user_model = get_user_model()
    deleter = user_model.objects.create_user(username="paginador", password="x")

    deleted_ids = []
    for index in range(30):
        deleted = _create_deleted_categoria(f"Paginacion Papelera {index}", deleter)
        deleted_ids.append(deleted.pk)

    fixed_deleted_at = timezone.make_aware(datetime(2026, 1, 15, 12, 0, 0))
    Categoria.all_objects.filter(pk__in=deleted_ids).update(deleted_at=fixed_deleted_at)

    response = auth_client.get(
        reverse("papelera_list"),
        {
            "model": _categoria_model_key(),
            "q": "Paginacion",
            "deleted_by": "paginador",
            "deleted_from": "2026-01-15",
            "deleted_to": "2026-01-15",
            "page": 2,
        },
    )

    assert response.status_code == 200
    content = response.content.decode()
    assert "q=Paginacion" in content
    assert "deleted_by=paginador" in content
    assert "deleted_from=2026-01-15" in content
    assert "deleted_to=2026-01-15" in content
    assert "page=1&amp;model=" in content or "page=1&model=" in content


@pytest.mark.django_db
def test_papelera_restore_preview_and_post_preserve_next_when_safe(client):
    user_model = get_user_model()
    actor = user_model.objects.create_user(username="deleter_restore", password="x")
    superuser = user_model.objects.create_superuser(
        username="super_restore",
        email="super_restore@example.com",
        password="x",
    )
    client.force_login(superuser)

    deleted = _create_deleted_categoria("Categoria Restore Safe", actor)
    model_key = _categoria_model_key()
    next_url = f"{reverse('papelera_list')}?model={model_key}&q=Restore&page=2"
    preview_url = reverse(
        "papelera_preview_restore",
        kwargs={
            "app_label": Categoria._meta.app_label,
            "model_name": Categoria._meta.model_name,
            "pk": deleted.pk,
        },
    )
    restore_url = reverse(
        "papelera_restore",
        kwargs={
            "app_label": Categoria._meta.app_label,
            "model_name": Categoria._meta.model_name,
            "pk": deleted.pk,
        },
    )

    preview_response = client.get(preview_url, {"next": next_url})
    assert preview_response.status_code == 200
    assert preview_response.context["back_url"] == next_url
    assert preview_response.context["next_url"] == next_url

    restore_response = client.post(
        restore_url,
        {"confirmed": "1", "next": next_url},
    )
    assert restore_response.status_code == 302
    assert restore_response["Location"] == next_url


@pytest.mark.django_db
def test_papelera_restore_ignores_unsafe_next(client):
    user_model = get_user_model()
    actor = user_model.objects.create_user(username="deleter_unsafe", password="x")
    superuser = user_model.objects.create_superuser(
        username="super_unsafe",
        email="super_unsafe@example.com",
        password="x",
    )
    client.force_login(superuser)

    deleted = _create_deleted_categoria("Categoria Restore Unsafe", actor)
    model_key = _categoria_model_key()
    restore_url = reverse(
        "papelera_restore",
        kwargs={
            "app_label": Categoria._meta.app_label,
            "model_name": Categoria._meta.model_name,
            "pk": deleted.pk,
        },
    )

    restore_response = client.post(
        restore_url,
        {"confirmed": "1", "next": "https://evil.example/fake"},
    )
    assert restore_response.status_code == 302
    assert (
        restore_response["Location"] == f"{reverse('papelera_list')}?model={model_key}"
    )


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
