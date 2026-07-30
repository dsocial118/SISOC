import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.urls import reverse

from comedores.models import Comedor, HistorialValidacion


@pytest.mark.django_db
def test_comedor_validator_group_can_validate_a_comedor_without_dupla(client):
    """El grupo específico habilita validar sin integrar la dupla del comedor."""
    call_command("create_groups", verbosity=0)
    validator_group = Group.objects.get(name="Validador Comedores")
    user = get_user_model().objects.create_user(
        username="validador-comedores", password="test-password"
    )
    user.groups.add(validator_group)
    comedor_view_group, _ = Group.objects.get_or_create(name="Comedores Ver")
    user.groups.add(comedor_view_group)
    comedor = Comedor.objects.create(nombre="Comedor a validar")
    client.force_login(user)

    response = client.post(
        reverse("validar_comedor", kwargs={"pk": comedor.pk}),
        {"accion": "validar"},
    )

    assert response.status_code == 302
    comedor.refresh_from_db()
    assert comedor.estado_validacion == "Validado"
    assert HistorialValidacion.objects.filter(comedor=comedor, usuario=user).exists()


@pytest.mark.django_db
def test_comedor_validator_group_does_not_grant_detail_access(client):
    """El rol de validar no reemplaza los permisos de lectura del legajo."""
    call_command("create_groups", verbosity=0)
    validator_group = Group.objects.get(name="Validador Comedores")
    user = get_user_model().objects.create_user(
        username="validador-sin-lectura", password="test-password"
    )
    user.groups.add(validator_group)
    comedor = Comedor.objects.create(nombre="Comedor sin lectura")
    client.force_login(user)

    response = client.post(
        reverse("validar_comedor", kwargs={"pk": comedor.pk}),
        {"accion": "validar"},
    )

    assert response.status_code == 403
    comedor.refresh_from_db()
    assert comedor.estado_validacion == "Pendiente"
    assert not HistorialValidacion.objects.filter(comedor=comedor).exists()


@pytest.mark.django_db
def test_manual_validation_post_without_permission_does_not_change_comedor(client):
    """Ocultar la UI no reemplaza el control de autorización del servidor."""
    user = get_user_model().objects.create_user(
        username="sin-permiso-validacion", password="test-password"
    )
    comedor_view_group, _ = Group.objects.get_or_create(name="Comedores Ver")
    user.groups.add(comedor_view_group)
    comedor = Comedor.objects.create(nombre="Comedor sin permiso")
    client.force_login(user)

    response = client.post(
        reverse("validar_comedor", kwargs={"pk": comedor.pk}),
        {"accion": "validar"},
    )

    assert response.status_code == 302
    comedor.refresh_from_db()
    assert comedor.estado_validacion == "Pendiente"
    assert not HistorialValidacion.objects.filter(comedor=comedor).exists()
