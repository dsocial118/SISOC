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
from core.models import Provincia
from core.templatetags.custom_filters import has_perm_code
from core.decorators import permissions_any_required
from core.permissions.registry import resolve_permission_codes
from iam.services import user_has_permission_code
from organizaciones.models import Organizacion
from users.forms import CustomUserChangeForm, GroupForm, UserCreationForm
from users.models import AccesoComedorPWA
from users.services import UsuariosService
from users.services_group_permissions import sync_permissions_for_group
from users.temporary_passwords import store_temporary_password

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
    fresh_user = User.objects.get(pk=saved_user.pk)
    assert fresh_user.user_permissions.filter(id=permission.id).exists()
    assert user_has_permission_code(fresh_user, "comedores.delete_comedor") is True


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
def test_mobile_user_creation_generates_password_automatically():
    provincia = Provincia.objects.create(nombre="Neuquén")
    organizacion = Organizacion.objects.create(nombre="Organización Mobile")
    comedor = Comedor.objects.create(
        nombre="Espacio Mobile",
        provincia=provincia,
        organizacion=organizacion,
    )

    form = UserCreationForm(
        data={
            "username": "mobile_auto_pwd",
            "email": "mobile_auto_pwd@example.com",
            "es_representante_pwa": True,
            "tipo_asociacion_pwa": "organizacion",
            "organizaciones_pwa": [organizacion.id],
            "comedores_pwa": [comedor.id],
        }
    )

    assert form.is_valid(), form.errors
    user = form.save()

    assert form.generated_password
    assert user.check_password(form.generated_password) is True
    assert user.profile.must_change_password is True


@pytest.mark.django_db
def test_existing_user_keeps_password_when_gaining_mobile_access():
    provincia = Provincia.objects.create(nombre="Río Negro")
    organizacion = Organizacion.objects.create(nombre="Organización Existing")
    comedor = Comedor.objects.create(
        nombre="Espacio Existing",
        provincia=provincia,
        organizacion=organizacion,
    )
    user = User.objects.create_user(
        username="existing_mobile",
        email="existing_mobile@example.com",
        password="ClaveOriginal123!",
    )
    original_password_hash = user.password

    form = CustomUserChangeForm(
        instance=user,
        data={
            "username": user.username,
            "email": user.email,
            "password": "",
            "es_representante_pwa": True,
            "tipo_asociacion_pwa": "organizacion",
            "organizaciones_pwa": [organizacion.id],
            "comedores_pwa": [comedor.id],
        },
    )

    assert form.is_valid(), form.errors
    saved_user = form.save()

    saved_user.refresh_from_db()
    assert saved_user.password == original_password_hash
    assert saved_user.check_password("ClaveOriginal123!") is True
    assert saved_user.profile.must_change_password is False


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
    assert (
        "Ingresa tu email para recibir un enlace de recuperación."
        in response.content.decode("utf-8")
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
def test_password_reset_request_by_username_marks_pending_request():
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    organizacion = Organizacion.objects.create(nombre="Organización Reset")
    comedor = Comedor.objects.create(
        nombre="Espacio Reset",
        provincia=provincia,
        organizacion=organizacion,
    )
    user = User.objects.create_user(
        username="mobile_reset_request",
        email="mobile_reset_request@example.com",
        password="Secreta123!",
    )
    AccesoComedorPWA.objects.create(
        user=user,
        comedor=comedor,
        rol=AccesoComedorPWA.ROL_REPRESENTANTE,
        activo=True,
    )
    client = APIClient()

    response = client.post(
        "/api/users/password-reset/request/",
        {"username": "mobile_reset_request"},
        format="json",
    )

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.profile.password_reset_requested_at is not None


@pytest.mark.django_db
def test_password_reset_request_by_username_ignores_non_pwa_user():
    user = User.objects.create_user(
        username="web_only_reset_request",
        email="web_only_reset_request@example.com",
        password="Secreta123!",
    )
    client = APIClient()

    response = client.post(
        "/api/users/password-reset/request/",
        {"username": "web_only_reset_request"},
        format="json",
    )

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.profile.password_reset_requested_at is None


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
def test_user_update_view_shows_temporary_password(client):
    admin = User.objects.create_user(
        username="users_editor",
        email="users_editor@example.com",
        password="Secreta123!",
    )
    change_user_permission = Permission.objects.get(
        content_type__app_label="auth",
        codename="change_user",
    )
    admin.user_permissions.add(change_user_permission)

    user = User.objects.create_user(
        username="temp_pwd_user",
        email="temp_pwd@example.com",
        password="Secreta123!",
    )
    user.profile.must_change_password = True
    user.profile.save(update_fields=["must_change_password"])

    client.force_login(admin)
    session = client.session
    store_temporary_password(session, user_id=user.pk, password="Temporal123!")
    session.save()
    response = client.get(reverse("usuario_editar", kwargs={"pk": user.pk}))

    assert response.status_code == 200
    assert "Temporal123!" in response.content.decode("utf-8")


@pytest.mark.django_db
@override_settings(ROOT_URLCONF="tests.test_urls_pr1400_fixes")
def test_user_list_shows_reset_pending_indicator_when_reset_pending():
    admin = User.objects.create_user(
        username="users_admin_list",
        email="users_admin_list@example.com",
        password="Secreta123!",
    )
    view_user_permission = Permission.objects.get(
        content_type__app_label="auth",
        codename="view_user",
    )
    change_user_permission = Permission.objects.get(
        content_type__app_label="auth",
        codename="change_user",
    )
    admin.user_permissions.add(view_user_permission, change_user_permission)

    user = User.objects.create_user(
        username="pending_reset_user",
        email="pending_reset_user@example.com",
        password="Anterior123!",
    )
    user.profile.password_reset_requested_at = user.profile.fecha_creacion
    user.profile.save(update_fields=["password_reset_requested_at"])

    request = RequestFactory().get(reverse("usuarios"))
    request.user = admin

    context = UsuariosService.get_usuarios_list_context(request)
    listed_users = list(UsuariosService.get_filtered_usuarios(request))

    assert context["table_headers"][-1]["title"] == "Reset"
    assert context["table_fields"][-1]["name"] == "password_reset_requested_indicator"
    pending_user = next(item for item in listed_users if item.pk == user.pk)
    assert pending_user.password_reset_requested_indicator == "!"


@pytest.mark.django_db
@override_settings(ROOT_URLCONF="tests.test_urls_pr1400_fixes")
def test_user_list_hides_reset_column_for_view_only_user_even_with_pending_requests():
    admin = User.objects.create_user(
        username="users_view_only_pending",
        email="users_view_only_pending@example.com",
        password="Secreta123!",
    )
    view_user_permission = Permission.objects.get(
        content_type__app_label="auth",
        codename="view_user",
    )
    admin.user_permissions.add(view_user_permission)

    user = User.objects.create_user(
        username="pending_reset_hidden",
        email="pending_reset_hidden@example.com",
        password="Anterior123!",
    )
    user.profile.password_reset_requested_at = user.profile.fecha_creacion
    user.profile.save(update_fields=["password_reset_requested_at"])

    request = RequestFactory().get(reverse("usuarios"))
    request.user = admin

    context = UsuariosService.get_usuarios_list_context(request)

    assert all(header["title"] != "Reset" for header in context["table_headers"])
    assert all(
        field["name"] != "password_reset_requested_indicator"
        for field in context["table_fields"]
    )


@pytest.mark.django_db
def test_user_create_view_redirects_with_temporary_password_visible(
    client, monkeypatch
):
    provincia = Provincia.objects.create(nombre="Salta")
    organizacion = Organizacion.objects.create(nombre="Organización Visible")
    comedor = Comedor.objects.create(
        nombre="Espacio Visible",
        provincia=provincia,
        organizacion=organizacion,
    )
    admin = User.objects.create_user(
        username="users_creator",
        email="users_creator@example.com",
        password="Secreta123!",
    )
    add_user_permission = Permission.objects.get(
        content_type__app_label="auth",
        codename="add_user",
    )
    change_user_permission = Permission.objects.get(
        content_type__app_label="auth",
        codename="change_user",
    )
    monkeypatch.setattr("users.forms.get_random_string", lambda _: "Temporal123!")
    admin.user_permissions.add(add_user_permission)
    admin.user_permissions.add(change_user_permission)

    client.force_login(admin)
    response = client.post(
        reverse("usuario_crear"),
        data={
            "username": "mobile_visible",
            "email": "mobile_visible@example.com",
            "es_representante_pwa": True,
            "tipo_asociacion_pwa": "organizacion",
            "organizaciones_pwa": [organizacion.id],
            "comedores_pwa": [comedor.id],
        },
        follow=True,
    )

    assert response.status_code == 200
    created_user = User.objects.get(username="mobile_visible")
    assert created_user.check_password("Temporal123!") is True
    content = response.content.decode("utf-8")
    assert "Contraseña inicial generada: Temporal123!" in content
    assert "Contraseña temporal vigente:" in content


@pytest.mark.django_db
def test_user_list_hides_reset_column_when_no_pending_requests(client):
    admin = User.objects.create_user(
        username="users_admin_no_pending",
        email="users_admin_no_pending@example.com",
        password="Secreta123!",
    )
    view_user_permission = Permission.objects.get(
        content_type__app_label="auth",
        codename="view_user",
    )
    admin.user_permissions.add(view_user_permission)

    client.force_login(admin)
    response = client.get(reverse("usuarios"))

    assert response.status_code == 200
    assert all(
        header["title"] != "Reset" for header in response.context["table_headers"]
    )
    assert all(
        field["name"] != "password_reset_requested_indicator"
        for field in response.context["table_fields"]
    )


@pytest.mark.django_db
def test_user_update_view_shows_reset_alert_and_button_inside_mobile_card(client):
    admin = User.objects.create_user(
        username="users_admin_edit_reset",
        email="users_admin_edit_reset@example.com",
        password="Secreta123!",
    )
    change_user_permission = Permission.objects.get(
        content_type__app_label="auth",
        codename="change_user",
    )
    admin.user_permissions.add(change_user_permission)

    user = User.objects.create_user(
        username="pending_reset_edit",
        email="pending_reset_edit@example.com",
        password="Anterior123!",
    )
    user.profile.password_reset_requested_at = user.profile.fecha_creacion
    user.profile.save(update_fields=["password_reset_requested_at"])

    client.force_login(admin)
    response = client.get(reverse("usuario_editar", kwargs={"pk": user.pk}))

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "El usuario pidió el blanqueamiento de contraseña." in content
    assert "Resetear contraseña" in content
    assert (
        reverse("usuario_generar_password_temporal", kwargs={"pk": user.pk}) in content
    )


@pytest.mark.django_db
def test_user_update_view_handles_user_without_profile(client):
    admin = User.objects.create_user(
        username="users_editor_legacy",
        email="users_editor_legacy@example.com",
        password="Secreta123!",
    )
    change_user_permission = Permission.objects.get(
        content_type__app_label="auth",
        codename="change_user",
    )
    admin.user_permissions.add(change_user_permission)

    user = User.objects.create_user(
        username="legacy_without_profile",
        email="legacy_without_profile@example.com",
        password="Secreta123!",
    )
    user.profile.delete()

    client.force_login(admin)
    response = client.get(reverse("usuario_editar", kwargs={"pk": user.pk}))

    assert response.status_code == 200


@pytest.mark.django_db
def test_generate_temporary_password_view_resets_flags_and_redirects_to_edit(client):
    admin = User.objects.create_user(
        username="users_admin_reset",
        email="users_admin_reset@example.com",
        password="Secreta123!",
    )
    change_user_permission = Permission.objects.get(
        content_type__app_label="auth",
        codename="change_user",
    )
    admin.user_permissions.add(change_user_permission)

    provincia = Provincia.objects.create(nombre="Córdoba")
    organizacion = Organizacion.objects.create(nombre="Organización Pending")
    comedor = Comedor.objects.create(
        nombre="Espacio Pending",
        provincia=provincia,
        organizacion=organizacion,
    )
    user = User.objects.create_user(
        username="pending_reset_generate",
        email="pending_reset_generate@example.com",
        password="Anterior123!",
    )
    AccesoComedorPWA.objects.create(
        user=user,
        comedor=comedor,
        rol=AccesoComedorPWA.ROL_REPRESENTANTE,
        activo=True,
    )
    user.profile.password_reset_requested_at = user.profile.fecha_creacion
    user.profile.save(update_fields=["password_reset_requested_at"])

    client.force_login(admin)
    response = client.post(
        reverse("usuario_generar_password_temporal", kwargs={"pk": user.pk})
    )

    assert response.status_code in {302, 303}
    assert reverse("usuario_editar", kwargs={"pk": user.pk}) in response.url
    user.refresh_from_db()
    assert user.profile.password_reset_requested_at is None
    assert user.profile.must_change_password is True
    assert user.profile.temporary_password_plaintext
    assert user.check_password(user.profile.temporary_password_plaintext) is True


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

    assert user_has_permission_code(user, "comedores.view_comedor") is True

    request = RequestFactory().get("/fake")
    request.user = user

    @permissions_any_required(["comedores.view_comedor"])
    def _dummy_view(req):
        return "ok"

    assert _dummy_view(request) == "ok"


@pytest.mark.django_db
def test_template_has_perm_code_is_canonical_only():
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

    assert has_perm_code(user, "Comedores Ver") is False
    assert has_perm_code(user, "comedores.view_comedor") is True


@pytest.mark.django_db
def test_resolve_permission_codes_ignores_legacy_aliases():
    assert resolve_permission_codes(["Comedores Ver", "comedores.view_comedor"]) == (
        "comedores.view_comedor",
    )


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


@pytest.mark.django_db
def test_user_list_view_shows_actions_according_to_is_active(client):
    user = User.objects.create_user(
        username="users_reader_actions",
        email="users_reader_actions@example.com",
        password="Secreta123!",
    )
    view_user_permission = Permission.objects.get(
        content_type__app_label="auth",
        codename="view_user",
    )
    user.user_permissions.add(view_user_permission)

    active_user = User.objects.create_user(
        username="active_target",
        email="active_target@example.com",
        password="Secreta123!",
        is_active=True,
    )
    inactive_user = User.objects.create_user(
        username="inactive_target",
        email="inactive_target@example.com",
        password="Secreta123!",
        is_active=False,
    )

    client.force_login(user)
    response = client.get(reverse("usuarios"))
    items_by_username = {
        item["cells"][2]["content"]: item
        for item in response.context["user_table_items"]
    }

    active_item = items_by_username[active_user.username]
    inactive_item = items_by_username[inactive_user.username]

    assert [action["label"] for action in active_item["actions"]] == [
        "Editar",
        "Desactivar",
    ]
    assert [action["label"] for action in inactive_item["actions"]] == [
        "Editar",
        "Activar",
    ]


@pytest.mark.django_db
def test_usuarios_service_annotates_is_active_display_as_true_false():
    active_user = User.objects.create_user(
        username="active_display_user",
        email="active_display_user@example.com",
        password="Secreta123!",
        is_active=True,
    )
    inactive_user = User.objects.create_user(
        username="inactive_display_user",
        email="inactive_display_user@example.com",
        password="Secreta123!",
        is_active=False,
    )

    queryset = UsuariosService.get_usuarios_queryset()

    assert queryset.get(pk=active_user.pk).is_active_display == "true"
    assert queryset.get(pk=inactive_user.pk).is_active_display == "false"


@pytest.mark.django_db
def test_user_activate_view_reactivates_user_with_delete_permission(client):
    user = User.objects.create_user(
        username="users_admin_activate",
        email="users_admin_activate@example.com",
        password="Secreta123!",
    )
    delete_user_permission = Permission.objects.get(
        content_type__app_label="auth",
        codename="delete_user",
    )
    user.user_permissions.add(delete_user_permission)
    inactive_user = User.objects.create_user(
        username="inactive_to_activate",
        email="inactive_to_activate@example.com",
        password="Secreta123!",
        is_active=False,
    )

    client.force_login(user)
    get_response = client.get(
        reverse("usuario_activar", kwargs={"pk": inactive_user.pk})
    )
    post_response = client.post(
        reverse("usuario_activar", kwargs={"pk": inactive_user.pk})
    )

    assert get_response.status_code == 200
    assert post_response.status_code in {302, 303}
    inactive_user.refresh_from_db()
    assert inactive_user.is_active is True


@pytest.mark.django_db
def test_user_activate_view_returns_403_without_delete_permission(client):
    user = User.objects.create_user(
        username="users_without_delete_permission",
        email="users_without_delete_permission@example.com",
        password="Secreta123!",
    )
    inactive_user = User.objects.create_user(
        username="inactive_forbidden",
        email="inactive_forbidden@example.com",
        password="Secreta123!",
        is_active=False,
    )

    client.force_login(user)
    response = client.post(reverse("usuario_activar", kwargs={"pk": inactive_user.pk}))

    assert response.status_code == 403
    inactive_user.refresh_from_db()
    assert inactive_user.is_active is False
