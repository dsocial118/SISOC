import json
from datetime import date

import pytest
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.test import RequestFactory
from django.urls import reverse

from ciudadanos.models import Ciudadano
from core.models import Localidad, Municipio, Provincia
from users.forms import UserCreationForm
from users.models import ProfileTerritorialScope
from users.services import UsuariosService
from users.territorial_scope import apply_territorial_scope


def _create_role_permission(codename: str, name: str) -> Permission:
    content_type = ContentType.objects.get_for_model(Group)
    permission, _ = Permission.objects.get_or_create(
        content_type=content_type,
        codename=codename,
        defaults={"name": name},
    )
    return permission


def _geo_set(prefix="Geo"):
    provincia = Provincia.objects.create(nombre=f"{prefix} Provincia")
    municipio = Municipio.objects.create(
        nombre=f"{prefix} Municipio", provincia=provincia
    )
    localidad = Localidad.objects.create(
        nombre=f"{prefix} Localidad", municipio=municipio
    )
    return provincia, municipio, localidad


def _user_form_data(username, scopes, provincia=""):
    return {
        "username": username,
        "email": f"{username}@example.com",
        "password": "pass12345",
        "es_usuario_provincial": "on",
        "provincia": provincia,
        "territorial_scopes": json.dumps(scopes),
    }


def _crear_ciudadano(documento, provincia, municipio, localidad):
    return Ciudadano.objects.create(
        apellido="Perez",
        nombre=f"Ciudadano {documento}",
        fecha_nacimiento=date(2010, 1, 1),
        documento=documento,
        provincia=provincia,
        municipio=municipio,
        localidad=localidad,
    )


@pytest.mark.django_db
def test_usuario_provincial_sin_alcances_es_valido_y_no_crea_scope():
    form = UserCreationForm(
        data=_user_form_data("prov_sin_scopes", [], provincia=""),
    )

    assert form.is_valid(), form.errors
    user = form.save()

    user.profile.refresh_from_db()
    assert user.profile.es_usuario_provincial is True
    assert user.profile.provincia_id is None
    assert user.profile.territorial_scopes.count() == 0


@pytest.mark.django_db
def test_usuario_provincial_acepta_multiples_provincias():
    provincia_a, _, _ = _geo_set("Multi A")
    provincia_b, _, _ = _geo_set("Multi B")
    form = UserCreationForm(
        data=_user_form_data(
            "prov_multi",
            [
                {
                    "provincia_id": provincia_a.id,
                    "municipio_id": None,
                    "localidad_id": None,
                },
                {
                    "provincia_id": provincia_b.id,
                    "municipio_id": None,
                    "localidad_id": None,
                },
            ],
        ),
    )

    assert form.is_valid(), form.errors
    user = form.save()

    assert set(
        user.profile.territorial_scopes.values_list("provincia_id", flat=True)
    ) == {provincia_a.id, provincia_b.id}
    assert user.profile.provincia_id is None


@pytest.mark.django_db
def test_usuario_provincial_acepta_provincia_municipio():
    provincia, municipio, _ = _geo_set("Municipio Valido")
    form = UserCreationForm(
        data=_user_form_data(
            "prov_municipio",
            [
                {
                    "provincia_id": provincia.id,
                    "municipio_id": municipio.id,
                    "localidad_id": None,
                }
            ],
        ),
    )

    assert form.is_valid(), form.errors
    user = form.save()

    scope = user.profile.territorial_scopes.get()
    assert scope.provincia_id == provincia.id
    assert scope.municipio_id == municipio.id
    assert scope.localidad_id is None
    assert user.profile.provincia_id is None


@pytest.mark.django_db
def test_usuario_provincial_acepta_provincia_municipio_localidad():
    provincia, municipio, localidad = _geo_set("Localidad Valida")
    form = UserCreationForm(
        data=_user_form_data(
            "prov_localidad",
            [
                {
                    "provincia_id": provincia.id,
                    "municipio_id": municipio.id,
                    "localidad_id": localidad.id,
                }
            ],
        ),
    )

    assert form.is_valid(), form.errors
    user = form.save()

    scope = user.profile.territorial_scopes.get()
    assert scope.provincia_id == provincia.id
    assert scope.municipio_id == municipio.id
    assert scope.localidad_id == localidad.id


@pytest.mark.django_db
def test_usuario_provincial_rechaza_municipio_sin_provincia():
    _, municipio, _ = _geo_set("Municipio Sin Provincia")
    form = UserCreationForm(
        data=_user_form_data(
            "prov_municipio_sin_prov",
            [
                {
                    "provincia_id": None,
                    "municipio_id": municipio.id,
                    "localidad_id": None,
                }
            ],
        ),
    )

    assert not form.is_valid()
    assert "territorial_scopes" in form.errors


@pytest.mark.django_db
def test_usuario_provincial_rechaza_localidad_sin_municipio():
    provincia, _, localidad = _geo_set("Localidad Sin Municipio")
    form = UserCreationForm(
        data=_user_form_data(
            "prov_localidad_sin_muni",
            [
                {
                    "provincia_id": provincia.id,
                    "municipio_id": None,
                    "localidad_id": localidad.id,
                }
            ],
        ),
    )

    assert not form.is_valid()
    assert "territorial_scopes" in form.errors


@pytest.mark.django_db
def test_usuario_provincial_rechaza_municipio_de_otra_provincia():
    provincia_a, _, _ = _geo_set("Cruce Provincia")
    _, municipio_b, _ = _geo_set("Cruce Municipio")
    form = UserCreationForm(
        data=_user_form_data(
            "prov_municipio_cruzado",
            [
                {
                    "provincia_id": provincia_a.id,
                    "municipio_id": municipio_b.id,
                    "localidad_id": None,
                }
            ],
        ),
    )

    assert not form.is_valid()
    assert "territorial_scopes" in form.errors


@pytest.mark.django_db
def test_usuario_provincial_rechaza_localidad_de_otro_municipio():
    provincia, municipio_a, _ = _geo_set("Cruce Localidad A")
    _, _, localidad_b = _geo_set("Cruce Localidad B")
    form = UserCreationForm(
        data=_user_form_data(
            "prov_localidad_cruzada",
            [
                {
                    "provincia_id": provincia.id,
                    "municipio_id": municipio_a.id,
                    "localidad_id": localidad_b.id,
                }
            ],
        ),
    )

    assert not form.is_valid()
    assert "territorial_scopes" in form.errors


@pytest.mark.django_db
def test_usuario_provincial_rechaza_alcances_duplicados():
    provincia, municipio, _ = _geo_set("Duplicado")
    payload = {
        "provincia_id": provincia.id,
        "municipio_id": municipio.id,
        "localidad_id": None,
    }
    form = UserCreationForm(
        data=_user_form_data("prov_duplicado", [payload, payload]),
    )

    assert not form.is_valid()
    assert "territorial_scopes" in form.errors


@pytest.mark.django_db
def test_scope_municipio_no_incluye_otro_municipio():
    provincia, municipio_a, localidad_a = _geo_set("Scope Municipio A")
    municipio_b = Municipio.objects.create(
        nombre="Scope Municipio B", provincia=provincia
    )
    localidad_b = Localidad.objects.create(
        nombre="Scope Localidad B", municipio=municipio_b
    )
    user = User.objects.create_user(username="scope_municipio", password="pass")
    profile = user.profile
    profile.es_usuario_provincial = True
    profile.save()
    ProfileTerritorialScope.objects.create(
        profile=profile,
        provincia=provincia,
        municipio=municipio_a,
    )
    visible = _crear_ciudadano(101, provincia, municipio_a, localidad_a)
    oculto = _crear_ciudadano(102, provincia, municipio_b, localidad_b)

    qs = apply_territorial_scope(
        Ciudadano.objects.all(),
        user,
        provincia_lookup="provincia_id",
        municipio_lookup="municipio_id",
        localidad_lookup="localidad_id",
    )

    assert visible in qs
    assert oculto not in qs


@pytest.mark.django_db
def test_scope_localidad_no_incluye_otra_localidad():
    provincia, municipio, localidad_a = _geo_set("Scope Localidad A")
    localidad_b = Localidad.objects.create(
        nombre="Scope Localidad B", municipio=municipio
    )
    user = User.objects.create_user(username="scope_localidad", password="pass")
    profile = user.profile
    profile.es_usuario_provincial = True
    profile.save()
    ProfileTerritorialScope.objects.create(
        profile=profile,
        provincia=provincia,
        municipio=municipio,
        localidad=localidad_a,
    )
    visible = _crear_ciudadano(201, provincia, municipio, localidad_a)
    oculto = _crear_ciudadano(202, provincia, municipio, localidad_b)

    qs = apply_territorial_scope(
        Ciudadano.objects.all(),
        user,
        provincia_lookup="provincia_id",
        municipio_lookup="municipio_id",
        localidad_lookup="localidad_id",
    )

    assert visible in qs
    assert oculto not in qs


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
def test_user_list_without_delegation_scope_only_shows_self():
    """Deny-by-default: un actor no-superuser sin alcance delegable configurado
    solo se ve a sí mismo en el listado."""
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
    assert other_user.username not in usernames


@pytest.mark.django_db
def test_user_update_view_blocks_user_out_of_actor_scope(client):
    """Un actor con alcance configurado no puede editar (IDOR) un usuario cuyos
    grupos estan fuera de su alcance: la vista responde 404."""
    allowed_group = Group.objects.create(name="Grupo Editable")
    denied_group = Group.objects.create(name="Grupo Fuera de Alcance")

    actor = User.objects.create_user(username="editor_acotado", password="secret")
    change_user_permission = Permission.objects.get(
        content_type__app_label="auth",
        codename="change_user",
    )
    actor.user_permissions.add(change_user_permission)
    actor.profile.grupos_asignables.set([allowed_group])

    fuera = User.objects.create_user(username="fuera_de_alcance", password="secret")
    fuera.groups.set([denied_group])

    dentro = User.objects.create_user(username="dentro_de_alcance", password="secret")
    dentro.groups.set([allowed_group])

    client.force_login(actor)

    resp_fuera = client.get(reverse("usuario_editar", kwargs={"pk": fuera.pk}))
    assert resp_fuera.status_code == 404

    resp_dentro = client.get(reverse("usuario_editar", kwargs={"pk": dentro.pk}))
    assert resp_dentro.status_code == 200


def _import_row_data(correo):
    return {
        "nombre": "Nombre",
        "apellido": "Apellido",
        "correo": correo,
        "permisos": "",
        "provincias": "",
        "rol": "TERRITORIAL",
    }


@pytest.mark.django_db
def test_import_pwa_crea_usuario_sin_staff():
    from users.models import UserImportJob
    from users.services_user_import import process_single_user_import_row

    admin = User.objects.create_user(username="import_admin_pwa", password="x")
    job = UserImportJob(
        requested_by=admin,
        original_filename="usuarios.xlsx",
        send_credentials=False,
        is_pwa_import=True,
    )

    result = process_single_user_import_row(
        row_data=_import_row_data("pwa.user@example.com"),
        job=job,
    )

    from users.models import UserImportJobRow

    assert result["status"] == UserImportJobRow.Status.CREATED
    creado = User.objects.get(email="pwa.user@example.com")
    assert creado.is_staff is False
    assert creado.is_active is True


@pytest.mark.django_db
def test_import_no_pwa_crea_usuario_staff():
    from users.models import UserImportJob
    from users.services_user_import import process_single_user_import_row

    admin = User.objects.create_user(username="import_admin_staff", password="x")
    job = UserImportJob(
        requested_by=admin,
        original_filename="usuarios.xlsx",
        send_credentials=False,
        is_pwa_import=False,
    )

    process_single_user_import_row(
        row_data=_import_row_data("staff.user@example.com"),
        job=job,
    )

    creado = User.objects.get(email="staff.user@example.com")
    assert creado.is_staff is True
    assert creado.is_active is True
