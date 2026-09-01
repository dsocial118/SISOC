import json
import re

import pytest
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.test import RequestFactory
from django.urls import reverse

from centrodeinfancia.models import AccesoCDI, CentroDeInfancia, Trabajador
from core.constants import UserGroups
from core.models import Localidad, Municipio, Provincia
from users.forms import CustomUserChangeForm, UserCreationForm
from users.models import ProfileTerritorialScope
from users.services import UsuariosService
from users.territorial_scope import apply_territorial_scope
from users.views_export import UserExportView


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
        "tipo_usuario": "interno",
        "es_usuario_provincial": "on",
        "provincia": provincia,
        "territorial_scopes": json.dumps(scopes),
    }


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
def test_alta_usuario_persiste_datos_identificatorios_y_tipo():
    data = _user_form_data("usuario-identificado", [])
    data.pop("es_usuario_provincial")
    data.update(
        {
            "dni": "12345678",
            "cuil": "20-12345678-3",
            "tipo_usuario": "provincial",
        }
    )

    form = UserCreationForm(data=data)

    assert form.is_valid(), form.errors
    user = form.save()

    user.profile.refresh_from_db()
    assert user.profile.dni == "12345678"
    assert user.profile.cuil == "20-12345678-3"
    assert user.profile.tipo_usuario == "provincial"
    assert user.profile.es_usuario_provincial is False


@pytest.mark.django_db
def test_alta_usuario_requiere_tipo_usuario():
    data = _user_form_data("usuario-sin-tipo", [])
    data.pop("tipo_usuario")

    form = UserCreationForm(data=data)

    assert not form.is_valid()
    assert "tipo_usuario" in form.errors


@pytest.mark.django_db
def test_alta_usuario_muestra_campos_identificatorios(client):
    actor = User.objects.create_user(username="admin-usuarios", password="secret")
    actor.user_permissions.add(
        Permission.objects.get(content_type__app_label="auth", codename="add_user")
    )
    client.force_login(actor)

    response = client.get(reverse("usuario_crear"))

    assert response.status_code == 200
    assert b"DNI" in response.content
    assert b"CUIL" in response.content
    assert b"Tipo de usuario" in response.content
    assert b"Interno" in response.content
    assert b"Provincial" in response.content
    assert b"Externo" in response.content


@pytest.mark.django_db
def test_edicion_usuario_precarga_y_actualiza_datos_identificatorios_y_tipo():
    user = User.objects.create_user(username="usuario-edicion", password="pass12345")
    user.profile.dni = "11111111"
    user.profile.cuil = "20-11111111-1"
    user.profile.tipo_usuario = "interno"
    user.profile.save(update_fields=["dni", "cuil", "tipo_usuario"])

    form = CustomUserChangeForm(instance=user)

    assert form.fields["dni"].initial == "11111111"
    assert form.fields["cuil"].initial == "20-11111111-1"
    assert form.fields["tipo_usuario"].initial == "interno"

    form = CustomUserChangeForm(
        instance=user,
        data={
            "username": user.username,
            "email": "",
            "dni": "22222222",
            "cuil": "27-22222222-2",
            "tipo_usuario": "externo",
            "territorial_scopes": "[]",
        },
    )

    assert form.is_valid(), form.errors
    form.save()

    user.profile.refresh_from_db()
    assert user.profile.dni == "22222222"
    assert user.profile.cuil == "27-22222222-2"
    assert user.profile.tipo_usuario == "externo"


@pytest.mark.django_db
def test_edicion_usuario_requiere_tipo_usuario():
    user = User.objects.create_user(username="usuario-edicion-sin-tipo", password="x")

    form = CustomUserChangeForm(
        instance=user,
        data={
            "username": user.username,
            "email": "",
            "territorial_scopes": "[]",
        },
    )

    assert not form.is_valid()
    assert "tipo_usuario" in form.errors


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
            "tipo_usuario": "interno",
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
            "tipo_usuario": "interno",
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
def test_user_creation_form_accepts_egp_with_multiple_full_province_scopes():
    provincias = [
        Provincia.objects.create(nombre="Provincia EGP A"),
        Provincia.objects.create(nombre="Provincia EGP B"),
    ]
    actor = User.objects.create_user(
        username="equipo-nacional-multiscope", password="secret"
    )
    equipo = Group.objects.create(name=UserGroups.SIMEPI_EQUIPO_NACIONAL)
    egp = Group.objects.create(name=UserGroups.SIMEPI_EGP)
    actor.groups.add(equipo)
    data = _user_form_data(
        "egp-con-multiscope",
        [
            {
                "provincia_id": provincia.pk,
                "municipio_id": None,
                "localidad_id": None,
            }
            for provincia in provincias
        ],
    )
    data["groups"] = [egp.pk]

    form = UserCreationForm(actor=actor, data=data)

    assert form.is_valid(), form.errors
    user = form.save()
    assert set(
        user.profile.territorial_scopes.values_list("provincia_id", flat=True)
    ) == {provincia.pk for provincia in provincias}


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
            "tipo_usuario": "interno",
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
            "tipo_usuario": "interno",
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
@pytest.mark.parametrize(
    "grupo_nacional",
    [
        UserGroups.SIMEPI_ADMINISTRADOR,
        UserGroups.SIMEPI_EQUIPO_NACIONAL,
    ],
)
def test_user_list_nacional_puede_buscar_y_visualizar_todos_los_usuarios(
    grupo_nacional,
):
    request_factory = RequestFactory()
    grupo = Group.objects.create(name=grupo_nacional)
    actor = User.objects.create_user(
        username=f"nacional-{grupo_nacional}", password="secret"
    )
    actor.groups.add(grupo)
    visible = User.objects.create_user(username="usuario-visible-nacional")
    visible.groups.add(Group.objects.create(name="Grupo fuera de delegación"))

    request = request_factory.get("/usuarios/", {"username": "visible-nacional"})
    request.user = actor
    usernames = set(
        UsuariosService.get_filtered_usuarios(request).values_list(
            "username", flat=True
        )
    )

    assert visible.username in usernames


@pytest.mark.django_db
@pytest.mark.parametrize(
    "grupo_nacional",
    [
        UserGroups.SIMEPI_ADMINISTRADOR,
        UserGroups.SIMEPI_EQUIPO_NACIONAL,
    ],
)
def test_visibilidad_nacional_no_amplia_el_alcance_de_edicion(
    client,
    grupo_nacional,
):
    grupo = Group.objects.create(name=grupo_nacional)
    actor = User.objects.create_user(
        username=f"editor-nacional-{grupo_nacional}", password="secret"
    )
    actor.groups.add(grupo)
    actor.user_permissions.add(
        Permission.objects.get(
            content_type__app_label="auth",
            codename="change_user",
        )
    )
    fuera_de_alcance = User.objects.create_user(
        username="usuario-visible-no-editable",
        password="secret",
    )
    client.force_login(actor)

    response = client.get(reverse("usuario_editar", kwargs={"pk": fuera_de_alcance.pk}))

    assert response.status_code == 404


@pytest.mark.django_db
def test_visibilidad_nacional_no_amplia_la_exportacion_de_usuarios():
    request_factory = RequestFactory()
    grupo = Group.objects.create(name=UserGroups.SIMEPI_EQUIPO_NACIONAL)
    actor = User.objects.create_user(username="exportador-nacional", password="secret")
    actor.groups.add(grupo)
    fuera_de_alcance = User.objects.create_user(username="usuario-no-exportable")
    request = request_factory.get("/usuarios/exportar/")
    request.user = actor
    view = UserExportView()
    view.request = request

    usernames = set(view.get_queryset().values_list("username", flat=True))

    assert actor.username in usernames
    assert fuera_de_alcance.username not in usernames


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
def test_egp_solo_administra_usuarios_vinculados_a_su_provincia():
    provincia_propia = Provincia.objects.create(nombre="Usuarios EGP propia")
    provincia_ajena = Provincia.objects.create(nombre="Usuarios EGP ajena")
    centro_propio = CentroDeInfancia.objects.create(
        nombre="CDI usuarios propio",
        provincia=provincia_propia,
    )
    centro_ajeno = CentroDeInfancia.objects.create(
        nombre="CDI usuarios ajeno",
        provincia=provincia_ajena,
    )
    egp_group, _ = Group.objects.get_or_create(name=UserGroups.SIMEPI_EGP)
    referente_group, _ = Group.objects.get_or_create(
        name=UserGroups.CDI_REFERENTE_CENTRO
    )
    actor = User.objects.create_user(username="egp-usuarios", password="secret")
    actor.groups.add(egp_group)
    actor.profile.es_usuario_provincial = True
    actor.profile.provincia = provincia_propia
    actor.profile.save(update_fields=["es_usuario_provincial", "provincia"])
    ProfileTerritorialScope.objects.create(
        profile=actor.profile,
        provincia=provincia_propia,
    )

    referente_propio = User.objects.create_user(
        username="referente-propio", password="secret"
    )
    referente_propio.groups.add(referente_group)
    AccesoCDI.objects.create(user=referente_propio, centro=centro_propio)
    referente_ajeno = User.objects.create_user(
        username="referente-ajeno", password="secret"
    )
    referente_ajeno.groups.add(referente_group)
    AccesoCDI.objects.create(user=referente_ajeno, centro=centro_ajeno)

    request = RequestFactory().get("/usuarios/")
    request.user = actor
    usernames = set(
        UsuariosService.get_usuarios_en_alcance(request).values_list(
            "username", flat=True
        )
    )

    assert {"egp-usuarios", "referente-propio"} <= usernames
    assert "referente-ajeno" not in usernames


@pytest.mark.django_db
def test_referente_solo_administra_trabajadores_de_su_cdi():
    centro_propio = CentroDeInfancia.objects.create(nombre="Usuarios CDI propio")
    centro_ajeno = CentroDeInfancia.objects.create(nombre="Usuarios CDI ajeno")
    referente_group, _ = Group.objects.get_or_create(
        name=UserGroups.CDI_REFERENTE_CENTRO
    )
    trabajador_group, _ = Group.objects.get_or_create(name=UserGroups.CDI_TRABAJADOR)
    actor = User.objects.create_user(username="referente-usuarios", password="secret")
    actor.groups.add(referente_group)
    AccesoCDI.objects.create(user=actor, centro=centro_propio)

    trabajador_propio_user = User.objects.create_user(
        username="trabajador-propio", password="secret"
    )
    trabajador_propio_user.groups.add(trabajador_group)
    Trabajador.objects.create(
        centro=centro_propio,
        usuario=trabajador_propio_user,
        nombre="Trabajador",
        apellido="Propio",
    )
    trabajador_ajeno_user = User.objects.create_user(
        username="trabajador-ajeno", password="secret"
    )
    trabajador_ajeno_user.groups.add(trabajador_group)
    Trabajador.objects.create(
        centro=centro_ajeno,
        usuario=trabajador_ajeno_user,
        nombre="Trabajador",
        apellido="Ajeno",
    )

    request = RequestFactory().get("/usuarios/")
    request.user = actor
    usernames = set(
        UsuariosService.get_usuarios_en_alcance(request).values_list(
            "username", flat=True
        )
    )

    assert {"referente-usuarios", "trabajador-propio"} <= usernames
    assert "trabajador-ajeno" not in usernames


@pytest.mark.django_db
def test_egp_sin_provincia_solo_se_ve_a_si_mismo_en_usuarios():
    egp_group, _ = Group.objects.get_or_create(name=UserGroups.SIMEPI_EGP)
    referente_group, _ = Group.objects.get_or_create(
        name=UserGroups.CDI_REFERENTE_CENTRO
    )
    actor = User.objects.create_user(
        username="egp-usuarios-sin-provincia", password="secret"
    )
    actor.groups.add(egp_group)
    actor.profile.es_usuario_provincial = True
    actor.profile.save(update_fields=["es_usuario_provincial"])
    referente = User.objects.create_user(
        username="referente-no-habilitado", password="secret"
    )
    referente.groups.add(referente_group)
    AccesoCDI.objects.create(
        user=referente,
        centro=CentroDeInfancia.objects.create(nombre="CDI sin scope EGP"),
    )

    request = RequestFactory().get("/usuarios/")
    request.user = actor
    usernames = set(
        UsuariosService.get_usuarios_en_alcance(request).values_list(
            "username", flat=True
        )
    )

    assert usernames == {"egp-usuarios-sin-provincia"}


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


@pytest.mark.django_db
def test_actor_cdi_no_ve_ni_puede_enviar_campos_administrativos_en_alta(client):
    actor = User.objects.create_user(username="referente-cdi-abm", password="secret")
    referente = Group.objects.create(name=UserGroups.CDI_REFERENTE_CENTRO)
    trabajador = Group.objects.create(name=UserGroups.CDI_TRABAJADOR)
    referente.permissions.add(
        Permission.objects.get(content_type__app_label="auth", codename="add_user")
    )
    actor.groups.add(referente)
    permission = Permission.objects.get(
        content_type__app_label="auth",
        codename="change_user",
    )

    client.force_login(actor)

    response = client.get(reverse("usuario_crear"))

    assert response.status_code == 200
    assert b'id="mobile-access-card"' in response.content
    assert re.search(
        rb'<div\s+id="mobile-access-card"[^>]*\bhidden\b', response.content
    )
    assert b"Permisos directos" not in response.content
    assert b"Es Coordinador de Equipo" not in response.content
    assert b"Grupos que puede asignar" not in response.content
    assert b"Roles que puede asignar" not in response.content

    response = client.post(
        reverse("usuario_crear"),
        data={
            "username": "trabajador-cdi-restringido",
            "email": "trabajador-cdi@example.com",
            "password": "pass12345",
            "tipo_usuario": "interno",
            "groups": [trabajador.pk],
            "user_permissions": [permission.pk],
            "es_representante_pwa": "on",
            "es_coordinador": "on",
            "grupos_asignables": [trabajador.pk],
        },
    )

    assert response.status_code == 302
    created = User.objects.get(username="trabajador-cdi-restringido")
    assert not created.user_permissions.filter(pk=permission.pk).exists()
    assert created.profile.es_coordinador is False
    assert not created.profile.grupos_asignables.exists()
    assert not created.accesos_pwa.filter(activo=True).exists()


@pytest.mark.django_db
def test_actor_cdi_preserva_configuracion_administrativa_oculta_en_edicion(client):
    provincia = Provincia.objects.create(nombre="Provincia ABM EGP")
    centro = CentroDeInfancia.objects.create(
        nombre="CDI ABM EGP",
        provincia=provincia,
    )
    actor = User.objects.create_user(username="egp-cdi-abm", password="secret")
    egp = Group.objects.create(name=UserGroups.SIMEPI_EGP)
    referente = Group.objects.create(name=UserGroups.CDI_REFERENTE_CENTRO)
    egp.permissions.add(
        Permission.objects.get(content_type__app_label="auth", codename="change_user")
    )
    actor.groups.add(egp)
    actor.profile.es_usuario_provincial = True
    actor.profile.save(update_fields=["es_usuario_provincial"])
    ProfileTerritorialScope.objects.create(
        profile=actor.profile,
        provincia=provincia,
    )

    target = User.objects.create_user(username="referente-editado", password="secret")
    target.groups.add(referente)
    AccesoCDI.objects.create(user=target, centro=centro)
    direct_permission = Permission.objects.get(
        content_type__app_label="auth",
        codename="change_user",
    )
    forbidden_permission = Permission.objects.get(
        content_type__app_label="auth",
        codename="delete_user",
    )
    target.user_permissions.add(direct_permission)
    target.profile.grupos_asignables.add(referente)

    client.force_login(actor)
    response = client.post(
        reverse("usuario_editar", kwargs={"pk": target.pk}),
        data={
            "username": target.username,
            "email": target.email,
            "tipo_usuario": "interno",
            "groups": [referente.pk],
            "user_permissions": [forbidden_permission.pk],
            "grupos_asignables": [],
        },
    )

    assert response.status_code == 302
    target.refresh_from_db()
    assert target.user_permissions.filter(pk=direct_permission.pk).exists()
    assert not target.user_permissions.filter(pk=forbidden_permission.pk).exists()
    assert list(target.profile.grupos_asignables.values_list("id", flat=True)) == [
        referente.pk
    ]


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
    provincia_legacy = Provincia.objects.create(nombre="Provincia EGP legacy")
    actor = User.objects.create_user(username="import_equipo_scope", password="x")
    equipo = Group.objects.create(name=UserGroups.SIMEPI_EQUIPO_NACIONAL)
    egp = Group.objects.create(name=UserGroups.SIMEPI_EGP)
    actor.groups.add(equipo)
    existente = User.objects.create_user(
        username="egp-existente-import",
        email="egp.existente@example.com",
        password="x",
    )
    existente.profile.provincia = provincia_legacy
    existente.profile.save(update_fields=["provincia"])
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
    existente.profile.refresh_from_db()
    assert existente.groups.filter(pk=egp.pk).exists()
    assert existente.profile.es_usuario_provincial is True
    assert existente.profile.provincia_id == provincia.pk
    assert list(
        existente.profile.territorial_scopes.values_list("provincia_id", flat=True)
    ) == [provincia.pk]


@pytest.mark.django_db
def test_import_egp_sincroniza_multiples_scopes_provinciales():
    from users.models import UserImportJob
    from users.services_user_import import process_single_user_import_row

    provincias = [
        Provincia.objects.create(nombre="Provincia EGP import A"),
        Provincia.objects.create(nombre="Provincia EGP import B"),
    ]
    actor = User.objects.create_user(username="import_equipo_multi", password="x")
    equipo = Group.objects.create(name=UserGroups.SIMEPI_EQUIPO_NACIONAL)
    egp = Group.objects.create(name=UserGroups.SIMEPI_EGP)
    actor.groups.add(equipo)
    job = UserImportJob(
        requested_by=actor,
        original_filename="usuarios.xlsx",
        send_credentials=False,
        is_pwa_import=False,
    )
    row_data = _import_row_data("egp.multi.import@example.com")
    row_data["permisos"] = egp.name
    row_data["provincias"] = ";".join(provincia.nombre for provincia in provincias)

    process_single_user_import_row(row_data=row_data, job=job)

    user = User.objects.get(email="egp.multi.import@example.com")
    assert set(
        user.profile.territorial_scopes.values_list("provincia_id", flat=True)
    ) == {provincia.pk for provincia in provincias}


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
