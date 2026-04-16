import pytest
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.test import RequestFactory

from users.forms import UserCreationForm
from users.services import UsuariosService


def _create_role_permission(codename: str, name: str) -> Permission:
    content_type = ContentType.objects.get_for_model(Group)
    permission, _ = Permission.objects.get_or_create(
        content_type=content_type,
        codename=codename,
        defaults={"name": name},
    )
    return permission


@pytest.mark.django_db
def test_user_creation_form_limits_groups_and_roles_by_actor_scope():
    actor = User.objects.create_user(username="actor", password="secret")
    allowed_group = Group.objects.create(name="Grupo permitido")
    forbidden_group = Group.objects.create(name="Grupo no permitido")
    allowed_role = _create_role_permission("role_vat_allowed", "Role VAT Allowed")
    forbidden_role = _create_role_permission("role_vat_forbidden", "Role VAT Forbidden")

    actor.profile.grupos_asignables.set([allowed_group])
    actor.profile.roles_asignables.set([allowed_role])

    form = UserCreationForm(
        actor=actor,
        data={
            "username": "nuevo_usuario",
            "email": "nuevo@example.com",
            "password": "pass12345",
            "groups": [allowed_group.pk, forbidden_group.pk],
            "user_permissions": [allowed_role.pk, forbidden_role.pk],
            "grupos_asignables": [allowed_group.pk, forbidden_group.pk],
            "roles_asignables": [allowed_role.pk, forbidden_role.pk],
        },
    )

    assert not form.is_valid()
    assert "groups" in form.errors
    assert "user_permissions" in form.errors
    assert "grupos_asignables" in form.errors
    assert "roles_asignables" in form.errors


@pytest.mark.django_db
def test_user_creation_form_persists_assignable_scope_in_profile():
    actor = User.objects.create_superuser(
        username="superadmin",
        email="superadmin@example.com",
        password="secret",
    )
    assignable_group = Group.objects.create(name="VAT Referente")
    assignable_role = _create_role_permission(
        "role_vat_referente", "Role VAT Referente"
    )

    form = UserCreationForm(
        actor=actor,
        data={
            "username": "delegador",
            "email": "delegador@example.com",
            "password": "pass12345",
            "groups": [assignable_group.pk],
            "user_permissions": [assignable_role.pk],
            "grupos_asignables": [assignable_group.pk],
            "roles_asignables": [assignable_role.pk],
        },
    )

    assert form.is_valid(), form.errors
    created_user = form.save()

    assert list(
        created_user.profile.grupos_asignables.values_list("id", flat=True)
    ) == [assignable_group.id]
    assert list(created_user.profile.roles_asignables.values_list("id", flat=True)) == [
        assignable_role.id
    ]


@pytest.mark.django_db
def test_user_list_is_scoped_by_actor_delegation_scope():
    request_factory = RequestFactory()

    actor = User.objects.create_user(username="delegador", password="secret")
    allowed_group = Group.objects.create(name="VAT Permitido")
    denied_group = Group.objects.create(name="Otro Modulo")
    allowed_role = _create_role_permission("role_vat_scope", "Role VAT Scope")
    denied_role = _create_role_permission("role_other_scope", "Role Other Scope")

    actor.profile.grupos_asignables.set([allowed_group])
    actor.profile.roles_asignables.set([allowed_role])

    visible_user = User.objects.create_user(username="visible", password="secret")
    visible_user.groups.set([allowed_group])
    visible_user.user_permissions.set([allowed_role])

    hidden_by_group = User.objects.create_user(
        username="hidden_group", password="secret"
    )
    hidden_by_group.groups.set([denied_group])
    hidden_by_group.user_permissions.set([allowed_role])

    hidden_by_role = User.objects.create_user(username="hidden_role", password="secret")
    hidden_by_role.groups.set([allowed_group])
    hidden_by_role.user_permissions.set([denied_role])

    request = request_factory.get("/usuarios/")
    request.user = actor
    queryset = UsuariosService.get_filtered_usuarios(request)
    usernames = set(queryset.values_list("username", flat=True))

    assert "delegador" in usernames
    assert "visible" in usernames
    assert "hidden_group" not in usernames
    assert "hidden_role" not in usernames


@pytest.mark.django_db
def test_user_list_with_only_group_scope_does_not_hide_users_without_roles():
    request_factory = RequestFactory()

    actor = User.objects.create_user(username="delegador_grupos", password="secret")
    allowed_group = Group.objects.create(name="Grupo VAT")
    denied_group = Group.objects.create(name="Grupo externo")
    direct_role = _create_role_permission("role_vat_direct", "Role VAT Direct")

    actor.profile.grupos_asignables.set([allowed_group])

    visible_user = User.objects.create_user(
        username="visible_solo_grupo", password="secret"
    )
    visible_user.groups.set([allowed_group])
    visible_user.user_permissions.set([direct_role])

    hidden_user = User.objects.create_user(
        username="oculto_solo_grupo", password="secret"
    )
    hidden_user.groups.set([denied_group])
    hidden_user.user_permissions.set([direct_role])

    request = request_factory.get("/usuarios/")
    request.user = actor
    usernames = set(
        UsuariosService.get_filtered_usuarios(request).values_list(
            "username", flat=True
        )
    )

    assert "delegador_grupos" in usernames
    assert "visible_solo_grupo" in usernames
    assert "oculto_solo_grupo" not in usernames


@pytest.mark.django_db
def test_user_list_with_only_role_scope_does_not_hide_users_with_allowed_groups():
    request_factory = RequestFactory()

    actor = User.objects.create_user(username="delegador_roles", password="secret")
    allowed_group = Group.objects.create(name="Grupo permitido roles")
    denied_role = _create_role_permission("role_otro_scope", "Role Otro Scope")
    allowed_role = _create_role_permission("role_vat_role_scope", "Role VAT Role Scope")

    actor.profile.roles_asignables.set([allowed_role])

    visible_user = User.objects.create_user(
        username="visible_solo_role", password="secret"
    )
    visible_user.groups.set([allowed_group])
    visible_user.user_permissions.set([allowed_role])

    hidden_user = User.objects.create_user(
        username="oculto_solo_role", password="secret"
    )
    hidden_user.groups.set([allowed_group])
    hidden_user.user_permissions.set([denied_role])

    request = request_factory.get("/usuarios/")
    request.user = actor
    usernames = set(
        UsuariosService.get_filtered_usuarios(request).values_list(
            "username", flat=True
        )
    )

    assert "delegador_roles" in usernames
    assert "visible_solo_role" in usernames
    assert "oculto_solo_role" not in usernames


@pytest.mark.django_db
def test_user_list_without_delegation_scope_keeps_default_visibility():
    request_factory = RequestFactory()
    actor = User.objects.create_user(username="sin_scope", password="secret")
    other_user = User.objects.create_user(username="otro", password="secret")

    request = request_factory.get("/usuarios/")
    request.user = actor
    usernames = set(
        UsuariosService.get_filtered_usuarios(request).values_list(
            "username", flat=True
        )
    )

    assert "sin_scope" in usernames
    assert other_user.username in usernames
