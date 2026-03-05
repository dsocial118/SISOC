"""Tests de seguridad para usuarios/perfil e IAM auth flows."""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.tokens import default_token_generator
from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.test import RequestFactory, override_settings
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework.test import APIClient

from comedores.models import Comedor
from core.templatetags.custom_filters import has_perm_code
from core.decorators import permissions_any_required
from iam.services import user_has_role
from users.forms import CustomUserChangeForm, GroupForm, UserCreationForm
from users.services_group_permissions import sync_permissions_for_group

User = get_user_model()


@pytest.mark.django_db
def test_user_creation_form_requires_email():
    form = UserCreationForm(
        data={
            "username": "sinemail",
            "password": "Secreta123!",
        }
    )

    assert form.is_valid() is False
    assert "email" in form.errors


@pytest.mark.django_db
def test_custom_user_change_form_requires_email(user):
    form = CustomUserChangeForm(
        instance=user,
        data={
            "username": user.username,
            "email": "",
            "password": "",
        },
    )

    assert form.is_valid() is False
    assert "email" in form.errors


@pytest.mark.django_db
def test_group_form_assigns_permissions():
    content_type = ContentType.objects.get_for_model(Group)
    permission = Permission.objects.create(
        content_type=content_type,
        codename="test_comedores_editar",
        name="Comedores Editar",
    )

    form = GroupForm(
        data={
            "name": "Grupo Operativo Comedores",
            "permissions": [permission.id],
        }
    )

    assert form.is_valid(), form.errors
    group = form.save()
    assert group.permissions.filter(id=permission.id).exists()


@pytest.mark.django_db
def test_custom_user_change_form_assigns_direct_permissions(user):
    content_type = ContentType.objects.get_for_model(Comedor)
    permission, _ = Permission.objects.get_or_create(
        content_type=content_type,
        codename="delete_comedor",
        defaults={"name": "Can delete comedor"},
    )

    form = CustomUserChangeForm(
        instance=user,
        data={
            "username": user.username,
            "email": user.email,
            "password": "",
            "groups": [],
            "user_permissions": [permission.id],
        },
    )

    assert form.is_valid(), form.errors
    saved_user = form.save()
    assert saved_user.user_permissions.filter(id=permission.id).exists()
    assert user_has_role(saved_user, "Comedores Eliminar") is True


@pytest.mark.django_db
def test_user_creation_sets_first_login_password_flags():
    Group.objects.create(name="Usuario Ver")

    form = UserCreationForm(
        data={
            "username": "nuevo_user",
            "email": "nuevo@example.com",
            "password": "Secreta123!",
            "groups": [],
            "es_representante_pwa": False,
        }
    )

    assert form.is_valid(), form.errors
    user = form.save()
    profile = user.profile

    assert profile.must_change_password is True
    assert profile.initial_password_expires_at is not None
    assert profile.password_changed_at is None


@pytest.mark.django_db
def test_first_login_password_change_view_clears_flags(client):
    user = User.objects.create_user(
        username="first_login_user",
        email="first_login@example.com",
        password="Secreta123!",
    )
    user.profile.must_change_password = True
    user.profile.save(update_fields=["must_change_password"])

    client.force_login(user)
    response = client.post(
        reverse("password_change_required"),
        data={
            "new_password1": "NuevaClave123!",
            "new_password2": "NuevaClave123!",
        },
    )

    assert response.status_code in {302, 303}
    user.refresh_from_db()
    assert user.profile.must_change_password is False
    assert user.profile.initial_password_expires_at is None
    assert user.check_password("NuevaClave123!") is True


@pytest.mark.django_db
def test_first_login_middleware_redirects_when_password_change_required(client):
    user = User.objects.create_user(
        username="must_change",
        email="must_change@example.com",
        password="Secreta123!",
    )
    user.profile.must_change_password = True
    user.profile.save(update_fields=["must_change_password"])

    client.force_login(user)
    response = client.get("/")

    assert response.status_code in {302, 303}
    assert reverse("password_change_required") in response.url


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_password_reset_request_sends_email_for_existing_user():
    User.objects.create_user(
        username="reset_user",
        email="reset@example.com",
        password="Secreta123!",
    )
    client = APIClient()

    response = client.post(
        "/api/users/password-reset/request/",
        {"email": "reset@example.com"},
        format="json",
    )

    assert response.status_code == 200
    assert len(mail.outbox) == 1


@pytest.mark.django_db
def test_password_reset_form_uses_sisoc_template(client):
    response = client.get(reverse("password_reset"))
    assert response.status_code == 200
    assert "Ingresa tu email para recibir un enlace de recuperación." in response.content.decode(
        "utf-8"
    )


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_password_reset_request_hides_non_existing_user():
    client = APIClient()

    response = client.post(
        "/api/users/password-reset/request/",
        {"email": "missing@example.com"},
        format="json",
    )

    assert response.status_code == 200
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_password_reset_confirm_changes_password_and_clears_flags():
    user = User.objects.create_user(
        username="reset_confirm",
        email="reset_confirm@example.com",
        password="Anterior123!",
    )
    user.profile.must_change_password = True
    user.profile.save(update_fields=["must_change_password"])

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    client = APIClient()

    response = client.post(
        "/api/users/password-reset/confirm/",
        {
            "uid": uid,
            "token": token,
            "new_password": "NuevaClave123!",
        },
        format="json",
    )

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.check_password("NuevaClave123!") is True
    assert user.profile.must_change_password is False


@pytest.mark.django_db
def test_web_password_reset_confirm_clears_flags(client):
    user = User.objects.create_user(
        username="reset_web",
        email="reset_web@example.com",
        password="Anterior123!",
    )
    user.profile.must_change_password = True
    user.profile.save(update_fields=["must_change_password"])

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    response = client.post(
        reverse("password_reset_confirm", kwargs={"uidb64": uid, "token": token}),
        data={
            "new_password1": "NuevaClave123!",
            "new_password2": "NuevaClave123!",
        },
    )

    assert response.status_code in {302, 303}
    user.refresh_from_db()
    assert user.check_password("NuevaClave123!") is True
    assert user.profile.must_change_password is False


@pytest.mark.django_db
def test_group_required_uses_group_permissions():
    user = User.objects.create_user(
        username="role_user",
        email="role_user@example.com",
        password="Secreta123!",
    )
    group = Group.objects.create(name="Grupo Y")
    content_type = ContentType.objects.get_for_model(Comedor)
    permission, _ = Permission.objects.get_or_create(
        content_type=content_type,
        codename="view_comedor",
        defaults={"name": "Can view comedor"},
    )
    group.permissions.add(permission)
    user.groups.add(group)

    assert user_has_role(user, "Comedores Ver") is True

    request = RequestFactory().get("/fake")
    request.user = user

    @permissions_any_required(["Comedores Ver"])
    def _dummy_view(req):
        return "ok"

    assert _dummy_view(request) == "ok"


@pytest.mark.django_db
def test_template_has_perm_code_with_alias():
    user = User.objects.create_user(
        username="perm_alias_user",
        email="perm_alias_user@example.com",
        password="Secreta123!",
    )
    group = Group.objects.create(name="Comedores Ver")
    content_type = ContentType.objects.get_for_model(Comedor)
    permission, _ = Permission.objects.get_or_create(
        content_type=content_type,
        codename="view_comedor",
        defaults={"name": "Can view comedor"},
    )
    group.permissions.add(permission)
    user.groups.add(group)

    assert has_perm_code(user, "Comedores Ver") is True
    assert has_perm_code(user, "comedores.view_comedor") is True


@pytest.mark.django_db
def test_sync_permissions_for_bootstrap_group_assigns_comedor_view():
    group = Group.objects.create(name="Tecnico Comedor")
    sync_permissions_for_group(group)
    group.refresh_from_db()
    assert group.permissions.filter(
        content_type__app_label="comedores",
        codename="view_comedor",
    ).exists()


@pytest.mark.django_db
def test_user_list_view_allows_non_superuser_with_view_user_permission(client):
    user = User.objects.create_user(
        username="users_reader",
        email="users_reader@example.com",
        password="Secreta123!",
    )
    view_user_permission = Permission.objects.get(
        content_type__app_label="auth",
        codename="view_user",
    )
    user.user_permissions.add(view_user_permission)

    client.force_login(user)
    response = client.get(reverse("usuarios"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_user_export_requires_view_and_export_permissions(client):
    user = User.objects.create_user(
        username="users_exporter",
        email="users_exporter@example.com",
        password="Secreta123!",
    )
    view_user_permission = Permission.objects.get(
        content_type__app_label="auth",
        codename="view_user",
    )
    user.user_permissions.add(view_user_permission)

    client.force_login(user)
    response = client.get(reverse("usuarios_exportar"))
    assert response.status_code == 403

    group_content_type = ContentType.objects.get_for_model(Group)
    export_permission, _ = Permission.objects.get_or_create(
        content_type=group_content_type,
        codename="role_exportar_a_csv",
        defaults={"name": "Exportar a csv"},
    )
    user.user_permissions.add(export_permission)
    response = client.get(reverse("usuarios_exportar"))
    assert response.status_code == 200
