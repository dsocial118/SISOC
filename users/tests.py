import json
from datetime import date

import pytest
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.test import RequestFactory
from django.urls import reverse

from ciudadanos.models import Ciudadano
from core.constants import UserGroups
from core.models import Localidad, Municipio, Provincia
from users.forms import CustomUserChangeForm, UserCreationForm
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
def test_user_creation_form_rejects_egp_without_province_scope():
    actor = User.objects.create_user(username="equipo-nacional-form", password="secret")
    equipo = Group.objects.create(name=UserGroups.SIMEPI_EQUIPO_NACIONAL)
    egp = Group.objects.create(name=UserGroups.SIMEPI_EGP)
    actor.groups.add(equipo)

    form = UserCreationForm(
        actor=actor,
        data={
            "username": "egp-sin-scope",
            "email": "egp-sin-scope@example.com",
            "password": "pass12345",
            "groups": [egp.pk],
        },
    )

    assert not form.is_valid()
    assert "territorial_scopes" in form.errors


@pytest.mark.django_db
def test_user_creation_form_accepts_egp_with_single_province_scope():
    provincia = Provincia.objects.create(nombre="Provincia EGP formulario")
    actor = User.objects.create_user(
        username="equipo-nacional-scope", password="secret"
    )
    equipo = Group.objects.create(name=UserGroups.SIMEPI_EQUIPO_NACIONAL)
    egp = Group.objects.create(name=UserGroups.SIMEPI_EGP)
    actor.groups.add(equipo)
    data = _user_form_data(
        "egp-con-scope",
        [
            {
                "provincia_id": provincia.pk,
                "municipio_id": None,
                "localidad_id": None,
            }
        ],
    )
    data["groups"] = [egp.pk]

    form = UserCreationForm(actor=actor, data=data)

    assert form.is_valid(), form.errors
    user = form.save()
    assert user.profile.es_usuario_provincial is True
    assert user.profile.territorial_scopes.get().provincia_id == provincia.pk


@pytest.mark.django_db
def test_user_change_form_no_permite_quitar_scope_a_egp():
    provincia = Provincia.objects.create(nombre="Provincia EGP edición")
    actor = User.objects.create_user(
        username="equipo-nacional-edita", password="secret"
    )
    equipo = Group.objects.create(name=UserGroups.SIMEPI_EQUIPO_NACIONAL)
    egp = Group.objects.create(name=UserGroups.SIMEPI_EGP)
    actor.groups.add(equipo)
    target = User.objects.create_user(
        username="egp-editado",
        email="egp-editado@example.com",
        password="secret",
    )
    target.groups.add(egp)
    target.profile.es_usuario_provincial = True
    target.profile.save(update_fields=["es_usuario_provincial"])
    ProfileTerritorialScope.objects.create(profile=target.profile, provincia=provincia)

    form = CustomUserChangeForm(
        actor=actor,
        instance=target,
        data={
            "username": target.username,
            "email": target.email,
            "groups": [egp.pk],
            "territorial_scopes": "[]",
        },
    )

    assert not form.is_valid()
    assert "territorial_scopes" in form.errors


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
def test_user_list_scoped_actor_excludes_superusers():
    """Un actor con alcance configurado no debe ver a los superadministradores
    (que sin grupos/roles propios satisfacían el filtro de subconjunto)."""
    request_factory = RequestFactory()

    actor = User.objects.create_user(username="delegador_no_super", password="secret")
    allowed_group = Group.objects.create(name="Grupo Scope Sin Super")
    actor.profile.grupos_asignables.set([allowed_group])

    usuario_con_rol = User.objects.create_user(
        username="usuario_con_rol", password="secret"
    )
    usuario_con_rol.groups.set([allowed_group])

    User.objects.create_superuser(username="super_admin_x", password="secret")

    request = request_factory.get("/usuarios/")
    request.user = actor
    usernames = set(
        UsuariosService.get_filtered_usuarios(request).values_list(
            "username", flat=True
        )
    )

    assert "usuario_con_rol" in usernames
    assert "super_admin_x" not in usernames


@pytest.mark.django_db
def test_change_form_muestra_y_preserva_grupos_fuera_de_alcance():
    """Al editar, el actor con alcance VE los grupos actuales del usuario (aunque
    estén fuera de su alcance) y, al guardar, esos grupos se preservan."""
    actor = User.objects.create_user(username="actor_form_scope", password="secret")
    asignable = Group.objects.create(name="Grupo Asignable Form")
    fuera = Group.objects.create(name="Grupo Fuera Form")
    actor.profile.grupos_asignables.set([asignable])

    target = User.objects.create_user(username="target_form_scope", password="secret")
    target.groups.set([fuera])

    form = CustomUserChangeForm(instance=target, actor=actor)

    # Display: el grupo actual (fuera de alcance) y el asignable están disponibles.
    visibles = set(form.fields["groups"].queryset.values_list("id", flat=True))
    assert {asignable.id, fuera.id} <= visibles

    # Preservación: el actor asigna el grupo permitido; el fuera de alcance no se
    # pierde al guardar.
    form.cleaned_data = {
        "groups": list(Group.objects.filter(id=asignable.id)),
        "user_permissions": [],
    }
    form._aplicar_grupos_y_permisos(target)  # pylint: disable=protected-access

    assert set(target.groups.values_list("id", flat=True)) == {
        asignable.id,
        fuera.id,
    }


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
        "username": "",
        "permisos": "",
        "provincias": "",
        "rol": "TERRITORIAL",
        "accion_grupos": "",
    }


@pytest.mark.django_db
def test_import_pwa_crea_usuario_sin_staff():
    from comedores.models import Comedor
    from users.models import UserImportJob
    from users.services_user_import import process_single_user_import_row

    admin = User.objects.create_user(username="import_admin_pwa", password="x")
    comedor = Comedor.objects.create(nombre="Comedor PWA Staff")
    job = UserImportJob(
        requested_by=admin,
        original_filename="usuarios.xlsx",
        send_credentials=False,
        is_pwa_import=True,
    )

    row_data = _import_row_data("pwa.user@example.com")
    row_data["comedores"] = str(comedor.pk)

    result = process_single_user_import_row(
        row_data=row_data,
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


@pytest.mark.django_db
def test_import_actor_sin_delegacion_no_puede_asignar_grupos():
    from users.models import UserImportJob
    from users.services_user_import import process_single_user_import_row

    actor = User.objects.create_user(username="import_sin_delegacion", password="x")
    grupo = Group.objects.create(name="Grupo fuera de alcance import")
    job = UserImportJob(
        requested_by=actor,
        original_filename="usuarios.xlsx",
        send_credentials=False,
        is_pwa_import=False,
    )
    row_data = _import_row_data("sin.alcance@example.com")
    row_data["permisos"] = grupo.name

    with pytest.raises(ValidationError, match="No tiene permiso"):
        process_single_user_import_row(row_data=row_data, job=job)


@pytest.mark.django_db
def test_import_actor_sin_delegacion_preserva_grupos_existentes():
    from users.models import UserImportJob
    from users.services_user_import import process_single_user_import_row

    actor = User.objects.create_user(username="import_sin_scope_replace", password="x")
    grupo = Group.objects.create(name="Grupo existente fuera de alcance")
    existente = User.objects.create_user(
        username="usuario-grupo-preservado",
        email="grupo.preservado@example.com",
        password="x",
    )
    existente.groups.add(grupo)
    job = UserImportJob(
        requested_by=actor,
        original_filename="usuarios.xlsx",
        send_credentials=False,
        is_pwa_import=False,
    )
    row_data = _import_row_data(existente.email)
    row_data["username"] = existente.username
    row_data["accion_grupos"] = "reemplazar"

    process_single_user_import_row(row_data=row_data, job=job)

    assert existente.groups.filter(pk=grupo.pk).exists()


@pytest.mark.django_db
def test_import_egp_sin_provincia_es_rechazado():
    from users.models import UserImportJob
    from users.services_user_import import process_single_user_import_row

    actor = User.objects.create_user(username="import_equipo_nacional", password="x")
    equipo = Group.objects.create(name=UserGroups.SIMEPI_EQUIPO_NACIONAL)
    egp = Group.objects.create(name=UserGroups.SIMEPI_EGP)
    actor.groups.add(equipo)
    job = UserImportJob(
        requested_by=actor,
        original_filename="usuarios.xlsx",
        send_credentials=False,
        is_pwa_import=False,
    )
    row_data = _import_row_data("egp.import@example.com")
    row_data["permisos"] = egp.name

    with pytest.raises(ValidationError, match="provincia"):
        process_single_user_import_row(row_data=row_data, job=job)


@pytest.mark.django_db
def test_import_egp_existente_sincroniza_scope_provincial():
    from users.models import UserImportJob
    from users.services_user_import import process_single_user_import_row

    provincia = Provincia.objects.create(nombre="Provincia EGP import")
    actor = User.objects.create_user(username="import_equipo_scope", password="x")
    equipo = Group.objects.create(name=UserGroups.SIMEPI_EQUIPO_NACIONAL)
    egp = Group.objects.create(name=UserGroups.SIMEPI_EGP)
    actor.groups.add(equipo)
    existente = User.objects.create_user(
        username="egp-existente-import",
        email="egp.existente@example.com",
        password="x",
    )
    job = UserImportJob(
        requested_by=actor,
        original_filename="usuarios.xlsx",
        send_credentials=False,
        is_pwa_import=False,
    )
    row_data = _import_row_data(existente.email)
    row_data["accion_grupos"] = "agregar"
    row_data["permisos"] = egp.name
    row_data["provincias"] = provincia.nombre

    process_single_user_import_row(row_data=row_data, job=job)

    existente.refresh_from_db()
    assert existente.groups.filter(pk=egp.pk).exists()
    assert existente.profile.es_usuario_provincial is True
    assert list(
        existente.profile.territorial_scopes.values_list("provincia_id", flat=True)
    ) == [provincia.pk]


@pytest.mark.django_db
def test_import_username_configurable_se_usa_tal_cual():
    """Si la fila trae Username, se usa ese valor y no se autogenera."""
    from users.models import UserImportJob
    from users.services_user_import import process_single_user_import_row

    admin = User.objects.create_user(username="import_admin_username", password="x")
    job = UserImportJob(
        requested_by=admin,
        original_filename="usuarios.xlsx",
        send_credentials=False,
        is_pwa_import=False,
    )

    row_data = _import_row_data("con.username@example.com")
    row_data["username"] = "usuario.manual"

    process_single_user_import_row(row_data=row_data, job=job)

    creado = User.objects.get(email="con.username@example.com")
    assert creado.username == "usuario.manual"


@pytest.mark.django_db
def test_import_username_vacio_se_autogenera():
    """Si la fila no trae Username, se genera automaticamente a partir del nombre."""
    from users.models import UserImportJob
    from users.services_user_import import process_single_user_import_row

    admin = User.objects.create_user(username="import_admin_autouser", password="x")
    job = UserImportJob(
        requested_by=admin,
        original_filename="usuarios.xlsx",
        send_credentials=False,
        is_pwa_import=False,
    )

    process_single_user_import_row(
        row_data=_import_row_data("sin.username@example.com"), job=job
    )

    creado = User.objects.get(email="sin.username@example.com")
    assert creado.username == "apellido.nombre"


@pytest.mark.django_db
def test_import_username_renombra_usuario_existente_matcheado_por_correo():
    """Si una fila matchea un usuario existente por correo y trae un Username
    distinto al actual, el importador debe renombrar el usuario."""
    from users.models import UserImportJob
    from users.services_user_import import process_single_user_import_row

    admin = User.objects.create_user(username="import_admin_rename", password="x")
    existente = User.objects.create_user(
        username="gonzalez.pedro",
        email="pedro.gonzalez@example.com",
        password="x",
    )
    job = UserImportJob(
        requested_by=admin,
        original_filename="usuarios.xlsx",
        send_credentials=False,
        is_pwa_import=False,
    )

    row_data = _import_row_data("pedro.gonzalez@example.com")
    row_data["username"] = "pedrouser"
    row_data["accion_grupos"] = "agregar"

    process_single_user_import_row(row_data=row_data, job=job)

    existente.refresh_from_db()
    assert existente.username == "pedrouser"


@pytest.mark.django_db
def test_import_pwa_asigna_organizaciones_y_comedores():
    """Un usuario PWA importado con Organizaciones y Comedores queda con
    acceso a todos los comedores de esas organizaciones, mas los comedores
    puntuales indicados."""
    from organizaciones.models import Organizacion, TipoEntidad
    from comedores.models import Comedor
    from users.models import AccesoComedorPWA, UserImportJob
    from users.services_user_import import process_single_user_import_row

    admin = User.objects.create_user(username="import_admin_orgs", password="x")
    tipo = TipoEntidad.objects.create(nombre="Personeria Juridica")
    organizacion = Organizacion.objects.create(
        nombre="Org Importada", tipo_entidad=tipo
    )
    comedor_de_org = Comedor.objects.create(
        nombre="Comedor de Org", organizacion=organizacion
    )
    comedor_suelto = Comedor.objects.create(nombre="Comedor Suelto")

    job = UserImportJob(
        requested_by=admin,
        original_filename="usuarios.xlsx",
        send_credentials=False,
        is_pwa_import=True,
    )

    row_data = _import_row_data("pwa.multi@example.com")
    row_data["organizaciones"] = str(organizacion.pk)
    row_data["comedores"] = str(comedor_suelto.pk)

    process_single_user_import_row(row_data=row_data, job=job)

    creado = User.objects.get(email="pwa.multi@example.com")
    accesos = {
        acceso.comedor_id: acceso
        for acceso in AccesoComedorPWA.objects.filter(user=creado, activo=True)
    }
    assert accesos[comedor_de_org.pk].tipo_asociacion == (
        AccesoComedorPWA.TIPO_ASOCIACION_ORGANIZACION
    )
    assert accesos[comedor_de_org.pk].organizacion_id == organizacion.pk
    assert accesos[comedor_suelto.pk].tipo_asociacion == (
        AccesoComedorPWA.TIPO_ASOCIACION_ESPACIO
    )
    assert accesos[comedor_suelto.pk].organizacion_id is None


@pytest.mark.django_db
def test_import_pwa_permiso_autorizado_se_asigna_directo():
    """Un permiso de gestion PWA que el actor puede delegar se asigna como
    permiso directo del usuario, no como grupo."""
    from comedores.models import Comedor
    from users.models import UserImportJob
    from users.services_user_import import process_single_user_import_row

    admin = User.objects.create_superuser(
        username="import_admin_pwa_perm", password="x", email="admin@example.com"
    )
    comedor = Comedor.objects.create(nombre="Comedor PWA Permiso")

    job = UserImportJob(
        requested_by=admin,
        original_filename="usuarios.xlsx",
        send_credentials=False,
        is_pwa_import=True,
    )

    row_data = _import_row_data("pwa.permiso@example.com")
    row_data["permisos"] = "manage_nomina_pwa"
    row_data["comedores"] = str(comedor.pk)

    process_single_user_import_row(row_data=row_data, job=job)

    creado = User.objects.get(email="pwa.permiso@example.com")
    assert creado.has_perm("pwa.manage_nomina_pwa")
    assert creado.groups.count() == 0


@pytest.mark.django_db
def test_import_pwa_permiso_no_autorizado_lanza_error():
    """Si el actor no puede delegar el permiso PWA solicitado, la fila falla."""
    from django.core.exceptions import ValidationError
    from users.models import UserImportJob
    from users.services_user_import import process_single_user_import_row

    admin = User.objects.create_user(username="import_admin_sin_perm", password="x")

    job = UserImportJob(
        requested_by=admin,
        original_filename="usuarios.xlsx",
        send_credentials=False,
        is_pwa_import=True,
    )

    row_data = _import_row_data("pwa.denegado@example.com")
    row_data["permisos"] = "manage_nomina_pwa"

    with pytest.raises(ValidationError):
        process_single_user_import_row(row_data=row_data, job=job)


@pytest.mark.django_db
def test_import_pwa_sin_organizaciones_ni_comedores_lanza_error():
    """Un usuario PWA nuevo sin Organizaciones ni Comedores en la fila no debe
    crearse, porque quedaria sin ningun acceso PWA activo (no podria loguear)."""
    from django.core.exceptions import ValidationError
    from users.models import UserImportJob
    from users.services_user_import import process_single_user_import_row

    admin = User.objects.create_user(username="import_admin_sin_espacio", password="x")

    job = UserImportJob(
        requested_by=admin,
        original_filename="usuarios.xlsx",
        send_credentials=False,
        is_pwa_import=True,
    )

    row_data = _import_row_data("pwa.sin.espacio@example.com")

    with pytest.raises(ValidationError):
        process_single_user_import_row(row_data=row_data, job=job)

    assert not User.objects.filter(email="pwa.sin.espacio@example.com").exists()


@pytest.mark.django_db
def test_import_pwa_organizacion_sin_comedores_lanza_error():
    """Una Organizacion sin comedores asociados no otorga ningun acceso PWA
    real; la fila debe fallar en vez de crear un usuario inutilizable."""
    from django.core.exceptions import ValidationError
    from organizaciones.models import Organizacion, TipoEntidad
    from users.models import UserImportJob
    from users.services_user_import import process_single_user_import_row

    admin = User.objects.create_user(username="import_admin_org_vacia", password="x")
    tipo = TipoEntidad.objects.create(nombre="Personeria Juridica")
    organizacion_vacia = Organizacion.objects.create(
        nombre="Org Sin Comedores", tipo_entidad=tipo
    )

    job = UserImportJob(
        requested_by=admin,
        original_filename="usuarios.xlsx",
        send_credentials=False,
        is_pwa_import=True,
    )

    row_data = _import_row_data("pwa.org.vacia@example.com")
    row_data["organizaciones"] = str(organizacion_vacia.pk)

    with pytest.raises(ValidationError):
        process_single_user_import_row(row_data=row_data, job=job)

    assert not User.objects.filter(email="pwa.org.vacia@example.com").exists()


@pytest.mark.django_db
def test_import_pwa_organizacion_sin_comedores_no_borra_accesos_existentes():
    """Actualizar un usuario PWA existente con una Organizacion sin comedores
    no debe desactivar silenciosamente sus accesos PWA activos previos."""
    from django.core.exceptions import ValidationError
    from comedores.models import Comedor
    from organizaciones.models import Organizacion, TipoEntidad
    from users.models import AccesoComedorPWA, UserImportJob
    from users.services_pwa import sync_representante_accesses
    from users.services_user_import import process_single_user_import_row

    admin = User.objects.create_user(
        username="import_admin_org_vacia_update", password="x"
    )
    tipo = TipoEntidad.objects.create(nombre="Personeria Juridica")
    organizacion_vacia = Organizacion.objects.create(
        nombre="Org Sin Comedores Update", tipo_entidad=tipo
    )
    comedor_suelto = Comedor.objects.create(nombre="Comedor Suelto Update")

    existente = User.objects.create_user(
        username="pwa.existente", email="pwa.existente@example.com", password="x"
    )
    sync_representante_accesses(
        user=existente,
        access_specs=[
            {
                "comedor_id": comedor_suelto.pk,
                "tipo_asociacion": AccesoComedorPWA.TIPO_ASOCIACION_ESPACIO,
                "organizacion_id": None,
            }
        ],
        actor=admin,
    )

    job = UserImportJob(
        requested_by=admin,
        original_filename="usuarios.xlsx",
        send_credentials=False,
        is_pwa_import=True,
    )

    row_data = _import_row_data("pwa.existente@example.com")
    row_data["organizaciones"] = str(organizacion_vacia.pk)

    with pytest.raises(ValidationError):
        process_single_user_import_row(row_data=row_data, job=job)

    acceso = AccesoComedorPWA.objects.get(user=existente, comedor=comedor_suelto)
    assert acceso.activo is True


@pytest.mark.django_db
def test_import_pwa_username_configurable_se_usa_tal_cual():
    """Igual que en la importacion no-PWA: si la fila trae Username, se usa
    ese valor tal cual y no se autogenera a partir de nombre/apellido."""
    from comedores.models import Comedor
    from users.models import UserImportJob
    from users.services_user_import import process_single_user_import_row

    admin = User.objects.create_user(username="import_admin_pwa_username", password="x")
    comedor = Comedor.objects.create(nombre="Comedor PWA Username")

    job = UserImportJob(
        requested_by=admin,
        original_filename="usuarios.xlsx",
        send_credentials=False,
        is_pwa_import=True,
    )

    row_data = _import_row_data("pwa.con.username@example.com")
    row_data["username"] = "usuario.pwa.manual"
    row_data["comedores"] = str(comedor.pk)

    process_single_user_import_row(row_data=row_data, job=job)

    creado = User.objects.get(email="pwa.con.username@example.com")
    assert creado.username == "usuario.pwa.manual"


@pytest.mark.django_db
def test_import_pwa_grupo_autorizado_se_asigna():
    """En un import PWA, un token de 'Permisos' que matchea un grupo existente
    se resuelve como grupo, igual que en import no-PWA."""
    from comedores.models import Comedor
    from users.models import UserImportJob
    from users.services_user_import import process_single_user_import_row

    admin = User.objects.create_superuser(
        username="import_admin_pwa_grupo",
        password="x",
        email="admin_pwa_grupo@example.com",
    )
    grupo = Group.objects.create(name="Grupo PWA Test")
    comedor = Comedor.objects.create(nombre="Comedor PWA Grupo")

    job = UserImportJob(
        requested_by=admin,
        original_filename="usuarios.xlsx",
        send_credentials=False,
        is_pwa_import=True,
    )

    row_data = _import_row_data("pwa.grupo@example.com")
    row_data["permisos"] = "Grupo PWA Test"
    row_data["comedores"] = str(comedor.pk)

    process_single_user_import_row(row_data=row_data, job=job)

    creado = User.objects.get(email="pwa.grupo@example.com")
    assert grupo in creado.groups.all()


@pytest.mark.django_db
def test_import_no_pwa_permiso_autorizado_se_asigna_directo():
    """En un import no-PWA, un token de 'Permisos' que matchea un permiso PWA
    delegable por el actor se asigna como permiso directo (no requiere grupo)."""
    from users.models import UserImportJob
    from users.services_user_import import process_single_user_import_row

    admin = User.objects.create_superuser(
        username="import_admin_staff_perm",
        password="x",
        email="admin_staff_perm@example.com",
    )

    job = UserImportJob(
        requested_by=admin,
        original_filename="usuarios.xlsx",
        send_credentials=False,
        is_pwa_import=False,
    )

    row_data = _import_row_data("staff.permiso@example.com")
    row_data["permisos"] = "manage_nomina_pwa"

    process_single_user_import_row(row_data=row_data, job=job)

    creado = User.objects.get(email="staff.permiso@example.com")
    assert creado.has_perm("pwa.manage_nomina_pwa")
    assert creado.groups.count() == 0
    assert creado.is_staff is True


@pytest.mark.django_db
def test_import_pwa_mezcla_grupo_y_permiso():
    """Un mismo token 'Permisos' puede mezclar nombre de grupo y codename de
    permiso PWA separados por ';', tambien en filas PWA."""
    from comedores.models import Comedor
    from users.models import UserImportJob
    from users.services_user_import import process_single_user_import_row

    admin = User.objects.create_superuser(
        username="import_admin_pwa_mix", password="x", email="admin_pwa_mix@example.com"
    )
    grupo = Group.objects.create(name="Grupo Mix PWA")
    comedor = Comedor.objects.create(nombre="Comedor Mix PWA")

    job = UserImportJob(
        requested_by=admin,
        original_filename="usuarios.xlsx",
        send_credentials=False,
        is_pwa_import=True,
    )

    row_data = _import_row_data("pwa.mix@example.com")
    row_data["permisos"] = "Grupo Mix PWA;manage_nomina_pwa"
    row_data["comedores"] = str(comedor.pk)

    process_single_user_import_row(row_data=row_data, job=job)

    creado = User.objects.get(email="pwa.mix@example.com")
    assert grupo in creado.groups.all()
    assert creado.has_perm("pwa.manage_nomina_pwa")


@pytest.mark.django_db
def test_import_no_pwa_mezcla_grupo_y_permiso():
    """Igual que en PWA, una fila no-PWA puede mezclar grupo y permiso en el
    mismo token 'Permisos'."""
    from users.models import UserImportJob
    from users.services_user_import import process_single_user_import_row

    admin = User.objects.create_superuser(
        username="import_admin_staff_mix",
        password="x",
        email="admin_staff_mix@example.com",
    )
    grupo = Group.objects.create(name="Grupo Mix Staff")

    job = UserImportJob(
        requested_by=admin,
        original_filename="usuarios.xlsx",
        send_credentials=False,
        is_pwa_import=False,
    )

    row_data = _import_row_data("staff.mix@example.com")
    row_data["permisos"] = "Grupo Mix Staff;manage_nomina_pwa"

    process_single_user_import_row(row_data=row_data, job=job)

    creado = User.objects.get(email="staff.mix@example.com")
    assert grupo in creado.groups.all()
    assert creado.has_perm("pwa.manage_nomina_pwa")


@pytest.mark.django_db
def test_import_no_pwa_permiso_no_autorizado_lanza_error():
    """Igual que en import PWA: si el actor no puede delegar el permiso PWA
    solicitado, la fila falla aunque no sea import PWA."""
    from django.core.exceptions import ValidationError
    from users.models import UserImportJob
    from users.services_user_import import process_single_user_import_row

    admin = User.objects.create_user(
        username="import_admin_staff_sin_perm", password="x"
    )

    job = UserImportJob(
        requested_by=admin,
        original_filename="usuarios.xlsx",
        send_credentials=False,
        is_pwa_import=False,
    )

    row_data = _import_row_data("staff.denegado@example.com")
    row_data["permisos"] = "manage_nomina_pwa"

    with pytest.raises(ValidationError):
        process_single_user_import_row(row_data=row_data, job=job)


@pytest.mark.django_db
def test_import_token_no_matchea_grupo_ni_permiso_lanza_error():
    """Un token que no es ni un grupo existente ni un permiso PWA delegable
    lanza un error claro identificando el token."""
    from django.core.exceptions import ValidationError
    from users.models import UserImportJob
    from users.services_user_import import process_single_user_import_row

    admin = User.objects.create_user(
        username="import_admin_token_invalido", password="x"
    )

    job = UserImportJob(
        requested_by=admin,
        original_filename="usuarios.xlsx",
        send_credentials=False,
        is_pwa_import=False,
    )

    row_data = _import_row_data("token.invalido@example.com")
    row_data["permisos"] = "Grupo Que No Existe"

    with pytest.raises(ValidationError, match="no es un grupo existente ni un permiso"):
        process_single_user_import_row(row_data=row_data, job=job)
