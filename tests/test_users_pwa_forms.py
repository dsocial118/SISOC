"""Tests for test users pwa forms."""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from rest_framework.test import APIClient

from comedores.models import Comedor, Programas
from core.constants import UserGroups
from core.models import Provincia
from duplas.models import Dupla
from organizaciones.models import Organizacion
from users.forms import (
    BackofficeAuthenticationForm,
    CustomUserChangeForm,
    PWA_OPERATION_PERMISSION_FIELDS,
    UserCreationForm,
)
from users.models import (
    AccesoComedorPWA,
    AccesoOrganizacionPWA,
    AuditAccesoComedorPWA,
    CoordinadorEquipoTecnicoPWA,
    RelevadorCalleProvincia,
    TerritorialComedorProvincia,
)
from users.services_pwa import get_access_rows, is_pwa_user

MOBILE_RENDICION_PERMISSION_CODE = "rendicioncuentasmensual.manage_mobile_rendicion"


def test_user_creation_form_provincia_usa_select2():
    field = UserCreationForm.base_fields["provincia"]

    assert "select2" in field.widget.attrs["class"].split()


@pytest.mark.django_db
def test_restricted_actor_cannot_store_hidden_mobile_role():
    actor = get_user_model().objects.create_user(username="cdi_actor")
    group, _ = Group.objects.get_or_create(name=UserGroups.SIMEPI_ADMINISTRADOR)
    actor.groups.add(group)
    form = UserCreationForm(
        actor=actor,
        data={
            "username": "restricted_mobile_target",
            "tipo_usuario": "interno",
            "password": "Test-only-123!",
            "es_representante_pwa": True,
            "es_coordinador_equipo_tecnico_pwa": True,
            "puede_gestionar_rendiciones_mobile": True,
        },
    )
    assert form.is_valid(), form.errors
    user = form.save()
    user.profile.refresh_from_db()
    assert not user.profile.configuracion_mobile["es_coordinador_equipo_tecnico_pwa"]
    assert not user.profile.configuracion_mobile["puede_gestionar_rendiciones_mobile"]
    assert not is_pwa_user(user)


@pytest.fixture
def comedor(db):
    provincia = Provincia.objects.create(nombre="Mendoza")
    organizacion = Organizacion.objects.create(nombre="Organización Forms")
    return Comedor.objects.create(
        nombre="Comedor Forms",
        provincia=provincia,
        organizacion=organizacion,
    )


@pytest.fixture
def comedor_extra(db):
    provincia = Provincia.objects.create(nombre="San Juan")
    organizacion = Organizacion.objects.create(nombre="Organización Extra")
    return Comedor.objects.create(
        nombre="Comedor Extra",
        provincia=provincia,
        organizacion=organizacion,
    )


@pytest.fixture
def comedor_mismo_org(db, comedor):
    return Comedor.objects.create(
        nombre="Comedor Misma Org",
        provincia=comedor.provincia,
        organizacion=comedor.organizacion,
    )


@pytest.mark.django_db
def test_user_creation_form_requires_some_mobile_scope():
    form = UserCreationForm(
        data={
            "username": "rep_forms",
            "tipo_usuario": "interno",
            "email": "rep_forms@example.com",
            "es_representante_pwa": True,
        }
    )

    assert form.is_valid() is False
    assert "comedores_pwa" in form.errors


@pytest.mark.django_db
def test_user_creation_form_expands_organization_without_explicit_spaces(comedor):
    form = UserCreationForm(
        data={
            "username": "rep_forms_org",
            "tipo_usuario": "interno",
            "email": "rep_forms_org@example.com",
            "es_representante_pwa": True,
            "tipo_asociacion_pwa": AccesoComedorPWA.TIPO_ASOCIACION_ORGANIZACION,
            "organizaciones_pwa": [comedor.organizacion_id],
        }
    )

    assert form.is_valid(), form.errors
    user = form.save()

    assert AccesoComedorPWA.objects.filter(
        user=user,
        comedor=comedor,
        organizacion_id=comedor.organizacion_id,
        tipo_asociacion=AccesoComedorPWA.TIPO_ASOCIACION_ORGANIZACION,
        activo=True,
    ).exists()


@pytest.mark.django_db
def test_user_creation_form_creates_mobile_user_associated_to_organization(comedor):
    Group.objects.create(name="Usuario Ver")
    form = UserCreationForm(
        data={
            "username": "rep_forms_ok",
            "tipo_usuario": "interno",
            "email": "rep_forms_ok@example.com",
            "groups": [],
            "es_representante_pwa": True,
            "tipo_asociacion_pwa": AccesoComedorPWA.TIPO_ASOCIACION_ORGANIZACION,
            "organizaciones_pwa": [comedor.organizacion_id],
            "comedores_pwa": [comedor.id],
        }
    )

    assert form.is_valid(), form.errors
    user = form.save()

    assert user.is_staff is False
    assert user.groups.count() == 0
    assert form.generated_password
    assert user.check_password(form.generated_password) is True
    assert (
        AccesoComedorPWA.objects.filter(
            user=user,
            comedor=comedor,
            organizacion_id=comedor.organizacion_id,
            rol=AccesoComedorPWA.ROL_REPRESENTANTE,
            tipo_asociacion=AccesoComedorPWA.TIPO_ASOCIACION_ORGANIZACION,
            activo=True,
        ).exists()
        is True
    )


@pytest.mark.django_db
def test_user_creation_form_creates_read_only_coordinator_with_dynamic_team_scope(
    comedor, comedor_extra
):
    user_model = get_user_model()
    abogado = user_model.objects.create_user(username="abogado_form_coord")
    tecnico = user_model.objects.create_user(username="tecnico_form_coord")
    dupla = Dupla.objects.create(
        nombre="Dupla Forms Coordinador",
        estado="Activo",
        abogado=abogado,
    )
    dupla.tecnico.add(tecnico)
    comedor.dupla = dupla
    comedor.save(update_fields=["dupla"])

    form = UserCreationForm(
        data={
            "username": "coordinador_forms",
            "email": "coordinador_forms@example.com",
            "tipo_usuario": "interno",
            "es_representante_pwa": True,
            "es_coordinador_equipo_tecnico_pwa": True,
            "duplas_coordinador_pwa": [dupla.id],
            "comedores_adicionales_coordinador_pwa": [comedor_extra.id],
        }
    )

    assert form.is_valid(), form.errors
    user = form.save()
    scope = CoordinadorEquipoTecnicoPWA.objects.get(user=user)

    assert user.is_staff is False
    assert scope.duplas.get() == dupla
    assert scope.comedores_adicionales.get() == comedor_extra
    assert not AccesoComedorPWA.objects.filter(user=user, activo=True).exists()


@pytest.mark.django_db
@pytest.mark.parametrize("coordinator", [False, True])
def test_mobile_selections_survive_saved_suspension(comedor, coordinator):
    comedor.programa = Programas.objects.create(nombre="Abordaje Comunitario")
    comedor.save(update_fields=["programa"])
    abogado = get_user_model().objects.create_user(username="scope_abogado")
    dupla = Dupla.objects.create(
        nombre="Equipo scope", estado="Activo", abogado=abogado
    )
    data = {
        "username": "mobile_suspension",
        "tipo_usuario": "interno",
        "es_representante_pwa": True,
        "es_coordinador_equipo_tecnico_pwa": coordinator,
        "duplas_coordinador_pwa": [dupla.pk],
        "comedores_adicionales_coordinador_pwa": [comedor.pk],
        "comedores_pwa": [comedor.pk],
        "puede_gestionar_rendiciones_mobile": True,
        **{name: True for name in PWA_OPERATION_PERMISSION_FIELDS},
    }
    create = UserCreationForm(data=data)
    assert create.is_valid(), create.errors
    user = create.save()
    password = create.generated_password
    assert is_pwa_user(user)
    client = APIClient()
    credentials = {"username": user.username, "password": password}
    response = client.post("/api/users/login/", credentials, format="json")
    assert response.status_code == 200, response.data
    client.credentials(HTTP_AUTHORIZATION=f"Token {response.data['token']}")
    access_response = client.get(f"/api/comedores/{comedor.pk}/usuarios/")
    assert access_response.status_code == 200, access_response.data
    login = BackofficeAuthenticationForm(
        data={"username": user.username, "password": password}
    )
    assert not login.is_valid()
    assert "solo puede ingresar desde la PWA" in str(login.errors)

    permission_codes = [MOBILE_RENDICION_PERMISSION_CODE] + [
        code for code, _ in PWA_OPERATION_PERMISSION_FIELDS.values()
    ]
    if coordinator:
        assert not user.is_staff
        assert not user.groups.exists()
        assert not user.user_permissions.exists()

    data["es_representante_pwa"] = False
    suspend = CustomUserChangeForm(instance=user, data=data)
    assert suspend.is_valid(), suspend.errors
    suspend.save()
    user = get_user_model().objects.get(pk=user.pk)
    assert not is_pwa_user(user)
    assert all(not user.has_perm(code) for code in permission_codes)
    assert (
        client.post("/api/users/login/", credentials, format="json").status_code == 401
    )
    assert client.get(f"/api/comedores/{comedor.pk}/usuarios/").status_code in (
        403,
        404,
    )
    if coordinator:
        assert not BackofficeAuthenticationForm(data=credentials).is_valid()

    reopened = CustomUserChangeForm(instance=user)
    assert not reopened["es_representante_pwa"].value()
    assert reopened["es_coordinador_equipo_tecnico_pwa"].value() == coordinator
    for name in [
        "puede_gestionar_rendiciones_mobile",
        *PWA_OPERATION_PERMISSION_FIELDS,
    ]:
        assert reopened[name].value() is True
    for name, pk in [
        ("duplas_coordinador_pwa", dupla.pk),
        ("comedores_adicionales_coordinador_pwa", comedor.pk),
        ("comedores_pwa", comedor.pk),
    ]:
        assert str(pk) in {str(value) for value in reopened[name].value()}

    # A second save while suspended must not erase the stored choices.
    restored_data = {name: reopened[name].value() for name in data}
    resave = CustomUserChangeForm(instance=user, data=restored_data)
    assert resave.is_valid(), resave.errors
    resave.save()
    user = get_user_model().objects.get(pk=user.pk)
    restored_data["es_representante_pwa"] = True
    reactivate = CustomUserChangeForm(instance=user, data=restored_data)
    assert reactivate.is_valid(), reactivate.errors
    reactivate.save()
    user = get_user_model().objects.get(pk=user.pk)
    assert is_pwa_user(user)
    assert user.check_password(password)
    assert user.is_staff is False
    assert (
        client.post("/api/users/login/", credentials, format="json").status_code == 200
    )
    assert client.get(f"/api/comedores/{comedor.pk}/usuarios/").status_code == 200
    if coordinator:
        assert CoordinadorEquipoTecnicoPWA.objects.get(user=user).activo
        assert not get_access_rows(user).exists()
        assert not user.user_permissions.exists()
        assert (
            client.post(f"/api/comedores/{comedor.pk}/usuarios/", {}).status_code == 403
        )
    else:
        assert get_access_rows(user).filter(comedor=comedor).exists()
        assert all(user.has_perm(code) for code in permission_codes)


@pytest.mark.django_db
def test_user_creation_form_assigns_mobile_rendicion_permission_with_checkbox(comedor):
    form = UserCreationForm(
        data={
            "username": "rep_forms_rendicion",
            "tipo_usuario": "interno",
            "email": "rep_forms_rendicion@example.com",
            "es_representante_pwa": True,
            "puede_gestionar_rendiciones_mobile": True,
            "tipo_asociacion_pwa": AccesoComedorPWA.TIPO_ASOCIACION_ORGANIZACION,
            "organizaciones_pwa": [comedor.organizacion_id],
            "comedores_pwa": [comedor.id],
        }
    )

    assert form.is_valid(), form.errors
    user = form.save()

    assert user.has_perm(MOBILE_RENDICION_PERMISSION_CODE) is True


@pytest.mark.django_db
def test_coordinator_can_be_created_suspended_and_enabled_later():
    abogado = get_user_model().objects.create_user(username="pending_abogado")
    dupla = Dupla.objects.create(
        nombre="Equipo pendiente", estado="Activo", abogado=abogado
    )
    data = {
        "username": "pending_coordinator",
        "tipo_usuario": "interno",
        "password": "Test-only-123!",
        "es_representante_pwa": False,
        "es_coordinador_equipo_tecnico_pwa": True,
        "duplas_coordinador_pwa": [dupla.pk],
    }
    create = UserCreationForm(data=data)
    assert create.is_valid(), create.errors
    user = create.save()
    assert not is_pwa_user(user)
    data["es_representante_pwa"] = True
    data["password"] = ""
    edit = CustomUserChangeForm(instance=user, data=data)
    assert edit.is_valid(), edit.errors
    edit.save()
    assert is_pwa_user(get_user_model().objects.get(pk=user.pk))


@pytest.mark.django_db
@pytest.mark.parametrize("mobile_enabled", [True, False])
def test_existing_web_user_can_receive_coordinator_role(mobile_enabled):
    user = get_user_model().objects.create_user(username="web_existing")
    abogado = get_user_model().objects.create_user(username="web_abogado")
    dupla = Dupla.objects.create(nombre="Equipo web", estado="Activo", abogado=abogado)
    edit = CustomUserChangeForm(
        instance=user,
        data={
            "username": user.username,
            "tipo_usuario": "interno",
            "es_representante_pwa": mobile_enabled,
            "es_coordinador_equipo_tecnico_pwa": True,
            "duplas_coordinador_pwa": [dupla.pk],
        },
    )
    assert edit.is_valid(), edit.errors
    edit.save()
    user.refresh_from_db()
    scope = CoordinadorEquipoTecnicoPWA.objects.get(user=user)
    assert scope.activo is mobile_enabled
    assert scope.duplas.get() == dupla
    assert is_pwa_user(user) is mobile_enabled
    assert user.is_staff is False


@pytest.mark.django_db
def test_custom_user_change_form_deactivates_mobile_access(comedor):
    create_form = UserCreationForm(
        data={
            "username": "rep_edit",
            "tipo_usuario": "interno",
            "email": "rep_edit@example.com",
            "es_representante_pwa": True,
            "tipo_asociacion_pwa": AccesoComedorPWA.TIPO_ASOCIACION_ORGANIZACION,
            "organizaciones_pwa": [comedor.organizacion_id],
            "comedores_pwa": [comedor.id],
        }
    )
    assert create_form.is_valid(), create_form.errors
    user = create_form.save()

    edit_form = CustomUserChangeForm(
        instance=user,
        data={
            "username": user.username,
            "tipo_usuario": "interno",
            "email": user.email,
            "password": "",
            "es_representante_pwa": False,
            "tipo_asociacion_pwa": "",
            "organizaciones_pwa": [],
            "comedores_pwa": [],
        },
    )
    assert edit_form.is_valid(), edit_form.errors
    edit_form.save()

    assert (
        AccesoComedorPWA.objects.filter(
            user=user,
            comedor=comedor,
            rol=AccesoComedorPWA.ROL_REPRESENTANTE,
            activo=True,
        ).exists()
        is False
    )
    acceso = AccesoComedorPWA.objects.get(user=user, comedor=comedor)
    assert acceso.fecha_baja is not None
    assert AuditAccesoComedorPWA.objects.filter(
        acceso=acceso,
        accion=AuditAccesoComedorPWA.ACCION_DEACTIVATE,
    ).exists()


@pytest.mark.django_db
def test_custom_user_change_form_preserves_org_without_current_spaces(comedor):
    create_form = UserCreationForm(
        data={
            "username": "rep_org_without_spaces",
            "tipo_usuario": "interno",
            "email": "rep_org_without_spaces@example.com",
            "es_representante_pwa": True,
            "tipo_asociacion_pwa": AccesoComedorPWA.TIPO_ASOCIACION_ORGANIZACION,
            "organizaciones_pwa": [comedor.organizacion_id],
            "comedores_pwa": [comedor.id],
        }
    )
    assert create_form.is_valid(), create_form.errors
    user = create_form.save()
    organizacion_original = comedor.organizacion

    comedor.organizacion = Organizacion.objects.create(nombre="Organización Destino")
    comedor.save(update_fields=["organizacion"])

    initial_form = CustomUserChangeForm(instance=user)
    assert initial_form.fields["es_representante_pwa"].initial is True
    assert (
        initial_form.fields["tipo_asociacion_pwa"].initial
        == AccesoComedorPWA.TIPO_ASOCIACION_ORGANIZACION
    )

    edit_form = CustomUserChangeForm(
        instance=user,
        data={
            "username": user.username,
            "tipo_usuario": "interno",
            "email": "rep_org_updated@example.com",
            "password": "",
            "es_representante_pwa": True,
            "tipo_asociacion_pwa": AccesoComedorPWA.TIPO_ASOCIACION_ORGANIZACION,
            "organizaciones_pwa": [organizacion_original.id],
            "comedores_pwa": [],
        },
    )
    assert edit_form.is_valid(), edit_form.errors
    edit_form.save()

    assert AccesoOrganizacionPWA.objects.filter(
        user=user,
        organizacion=organizacion_original,
        activo=True,
    ).exists()

    comedor_nuevo = Comedor.objects.create(
        nombre="Comedor Incorporado Luego",
        provincia=comedor.provincia,
        organizacion=organizacion_original,
    )
    assert get_access_rows(user).filter(comedor=comedor_nuevo).exists()


@pytest.mark.django_db
def test_custom_user_change_form_can_remove_mobile_rendicion_permission(comedor):
    permission = Permission.objects.get(
        content_type__app_label="rendicioncuentasmensual",
        codename="manage_mobile_rendicion",
    )
    create_form = UserCreationForm(
        data={
            "username": "rep_edit_rendicion",
            "tipo_usuario": "interno",
            "email": "rep_edit_rendicion@example.com",
            "es_representante_pwa": True,
            "puede_gestionar_rendiciones_mobile": True,
            "tipo_asociacion_pwa": AccesoComedorPWA.TIPO_ASOCIACION_ORGANIZACION,
            "organizaciones_pwa": [comedor.organizacion_id],
            "comedores_pwa": [comedor.id],
        }
    )
    assert create_form.is_valid(), create_form.errors
    user = create_form.save()
    assert user.has_perm(MOBILE_RENDICION_PERMISSION_CODE) is True

    edit_form = CustomUserChangeForm(
        instance=user,
        data={
            "username": user.username,
            "tipo_usuario": "interno",
            "email": user.email,
            "password": "",
            "es_representante_pwa": True,
            "puede_gestionar_rendiciones_mobile": False,
            "tipo_asociacion_pwa": AccesoComedorPWA.TIPO_ASOCIACION_ORGANIZACION,
            "organizaciones_pwa": [comedor.organizacion_id],
            "comedores_pwa": [comedor.id],
        },
    )
    assert edit_form.is_valid(), edit_form.errors
    edit_form.save()
    user = type(user).objects.get(pk=user.pk)

    assert user.user_permissions.filter(pk=permission.pk).exists() is False
    assert user.has_perm(MOBILE_RENDICION_PERMISSION_CODE) is False


@pytest.mark.django_db
def test_custom_user_change_form_allows_disabling_mobile_even_if_post_keeps_hidden_values(
    comedor,
):
    create_form = UserCreationForm(
        data={
            "username": "rep_disable_hidden",
            "tipo_usuario": "interno",
            "email": "rep_disable_hidden@example.com",
            "es_representante_pwa": True,
            "tipo_asociacion_pwa": AccesoComedorPWA.TIPO_ASOCIACION_ORGANIZACION,
            "organizaciones_pwa": [comedor.organizacion_id],
            "comedores_pwa": [comedor.id],
        }
    )
    assert create_form.is_valid(), create_form.errors
    user = create_form.save()

    edit_form = CustomUserChangeForm(
        instance=user,
        data={
            "username": user.username,
            "tipo_usuario": "interno",
            "email": user.email,
            "password": "",
            "es_representante_pwa": False,
            "tipo_asociacion_pwa": AccesoComedorPWA.TIPO_ASOCIACION_ORGANIZACION,
            "organizaciones_pwa": [comedor.organizacion_id],
            "comedores_pwa": [comedor.id],
        },
    )

    assert edit_form.is_valid(), edit_form.errors
    edit_form.save()
    assert not AccesoComedorPWA.objects.filter(user=user, activo=True).exists()


@pytest.mark.django_db
def test_custom_user_change_form_allows_space_association_without_organizations(
    comedor, comedor_extra
):
    create_form = UserCreationForm(
        data={
            "username": "rep_space_edit",
            "tipo_usuario": "interno",
            "email": "rep_space_edit@example.com",
            "es_representante_pwa": True,
            "tipo_asociacion_pwa": AccesoComedorPWA.TIPO_ASOCIACION_ORGANIZACION,
            "organizaciones_pwa": [comedor.organizacion_id],
            "comedores_pwa": [comedor.id],
        }
    )
    assert create_form.is_valid(), create_form.errors
    user = create_form.save()

    edit_form = CustomUserChangeForm(
        instance=user,
        data={
            "username": user.username,
            "tipo_usuario": "interno",
            "email": user.email,
            "password": "",
            "es_representante_pwa": True,
            "tipo_asociacion_pwa": AccesoComedorPWA.TIPO_ASOCIACION_ESPACIO,
            "organizaciones_pwa": [],
            "comedores_pwa": [comedor_extra.id],
        },
    )

    assert edit_form.is_valid(), edit_form.errors
    edit_form.save()

    assert (
        AccesoComedorPWA.objects.filter(
            user=user,
            comedor=comedor_extra,
            rol=AccesoComedorPWA.ROL_REPRESENTANTE,
            tipo_asociacion=AccesoComedorPWA.TIPO_ASOCIACION_ESPACIO,
            activo=True,
        ).exists()
        is True
    )


@pytest.mark.django_db
def test_user_creation_form_allows_organization_plus_direct_space(
    comedor, comedor_extra
):
    form = UserCreationForm(
        data={
            "username": "rep_forms_mixed",
            "tipo_usuario": "interno",
            "email": "rep_forms_mixed@example.com",
            "es_representante_pwa": True,
            "organizaciones_pwa": [comedor.organizacion_id],
            "comedores_pwa": [comedor.id, comedor_extra.id],
        }
    )

    assert form.is_valid(), form.errors
    user = form.save()

    assert (
        AccesoComedorPWA.objects.filter(
            user=user,
            comedor=comedor,
            rol=AccesoComedorPWA.ROL_REPRESENTANTE,
            tipo_asociacion=AccesoComedorPWA.TIPO_ASOCIACION_ORGANIZACION,
            organizacion_id=comedor.organizacion_id,
            activo=True,
        ).exists()
        is True
    )
    assert (
        AccesoComedorPWA.objects.filter(
            user=user,
            comedor=comedor_extra,
            rol=AccesoComedorPWA.ROL_REPRESENTANTE,
            tipo_asociacion=AccesoComedorPWA.TIPO_ASOCIACION_ESPACIO,
            organizacion_id__isnull=True,
            activo=True,
        ).exists()
        is True
    )


@pytest.mark.django_db
def test_user_creation_form_includes_all_org_spaces_plus_external_space(
    comedor, comedor_mismo_org, comedor_extra
):
    form = UserCreationForm(
        data={
            "username": "rep_forms_partial_org",
            "tipo_usuario": "interno",
            "email": "rep_forms_partial_org@example.com",
            "es_representante_pwa": True,
            "organizaciones_pwa": [comedor.organizacion_id],
            "comedores_pwa": [comedor.id, comedor_extra.id],
        }
    )

    assert form.is_valid(), form.errors
    user = form.save()

    assert (
        AccesoComedorPWA.objects.filter(
            user=user,
            comedor=comedor,
            rol=AccesoComedorPWA.ROL_REPRESENTANTE,
            tipo_asociacion=AccesoComedorPWA.TIPO_ASOCIACION_ORGANIZACION,
            organizacion_id=comedor.organizacion_id,
            activo=True,
        ).exists()
        is True
    )
    assert (
        AccesoComedorPWA.objects.filter(
            user=user,
            comedor=comedor_mismo_org,
            tipo_asociacion=AccesoComedorPWA.TIPO_ASOCIACION_ORGANIZACION,
            organizacion_id=comedor.organizacion_id,
            activo=True,
        ).exists()
        is True
    )
    assert (
        AccesoComedorPWA.objects.filter(
            user=user,
            comedor=comedor_extra,
            rol=AccesoComedorPWA.ROL_REPRESENTANTE,
            tipo_asociacion=AccesoComedorPWA.TIPO_ASOCIACION_ESPACIO,
            organizacion_id__isnull=True,
            activo=True,
        ).exists()
        is True
    )


@pytest.mark.django_db
def test_user_creation_form_creates_territorial_with_provincia():
    provincia = Provincia.objects.create(nombre="Territorial Prov")
    form = UserCreationForm(
        data={
            "username": "territorial_ok",
            "email": "territorial_ok@example.com",
            "password": "Sisoc12345!",
            "tipo_usuario": "interno",
            "es_territorial_comedor": True,
            "provincias_territorial": [provincia.id],
        }
    )

    assert form.is_valid(), form.errors
    user = form.save()

    assert user.profile.es_territorial_comedor is True
    assert (
        TerritorialComedorProvincia.objects.filter(
            profile=user.profile,
            provincia=provincia,
        ).exists()
        is True
    )
    # Flag simple: el territorial es un usuario normal, no un mobile-only.
    assert user.check_password("Sisoc12345!") is True


@pytest.mark.django_db
def test_user_creation_form_territorial_requires_provincia():
    form = UserCreationForm(
        data={
            "username": "territorial_sin_prov",
            "email": "territorial_sin_prov@example.com",
            "password": "Sisoc12345!",
            "es_territorial_comedor": True,
        }
    )

    assert form.is_valid() is False
    assert "provincias_territorial" in form.errors


@pytest.mark.django_db
def test_user_creation_form_territorial_excludes_representante(comedor):
    form = UserCreationForm(
        data={
            "username": "territorial_y_rep",
            "email": "territorial_y_rep@example.com",
            "es_representante_pwa": True,
            "comedores_pwa": [comedor.id],
            "es_territorial_comedor": True,
            "provincias_territorial": [comedor.provincia_id],
        }
    )

    assert form.is_valid() is False
    assert "es_territorial_comedor" in form.errors


@pytest.mark.django_db
def test_custom_user_change_form_disables_territorial_clears_provincias():
    provincia = Provincia.objects.create(nombre="Territorial Edit Prov")
    create_form = UserCreationForm(
        data={
            "username": "territorial_edit",
            "email": "territorial_edit@example.com",
            "password": "Sisoc12345!",
            "tipo_usuario": "interno",
            "es_territorial_comedor": True,
            "provincias_territorial": [provincia.id],
        }
    )
    assert create_form.is_valid(), create_form.errors
    user = create_form.save()

    edit_form = CustomUserChangeForm(
        instance=user,
        data={
            "username": user.username,
            "email": user.email,
            "password": "",
            "tipo_usuario": "interno",
            "es_territorial_comedor": False,
        },
    )
    assert edit_form.is_valid(), edit_form.errors
    edit_form.save()

    user.profile.refresh_from_db()
    assert user.profile.es_territorial_comedor is False
    assert (
        TerritorialComedorProvincia.objects.filter(profile=user.profile).exists()
        is False
    )


@pytest.mark.django_db
def test_backoffice_authentication_form_rejects_mobile_user(comedor):
    create_form = UserCreationForm(
        data={
            "username": "rep_login_form",
            "tipo_usuario": "interno",
            "email": "rep_login_form@example.com",
            "es_representante_pwa": True,
            "tipo_asociacion_pwa": AccesoComedorPWA.TIPO_ASOCIACION_ORGANIZACION,
            "organizaciones_pwa": [comedor.organizacion_id],
            "comedores_pwa": [comedor.id],
        }
    )
    assert create_form.is_valid(), create_form.errors
    create_form.save()

    login_form = BackofficeAuthenticationForm(
        request=None,
        data={
            "username": "rep_login_form",
            "tipo_usuario": "interno",
            "password": create_form.generated_password,
        },
    )

    assert login_form.is_valid() is False
    assert "solo puede ingresar desde la PWA" in str(login_form.errors)


@pytest.mark.django_db
def test_user_creation_form_creates_relevador_calle_with_provincia():
    provincia = Provincia.objects.create(nombre="DataCalle Prov")
    form = UserCreationForm(
        data={
            "username": "relevador_ok",
            "email": "relevador_ok@example.com",
            "password": "Sisoc12345!",
            "tipo_usuario": "interno",
            "es_relevador_calle": True,
            "datacalle_rol": "entrevistador",
            "provincias_datacalle": [provincia.id],
        }
    )

    assert form.is_valid(), form.errors
    user = form.save()

    assert user.profile.es_relevador_calle is True
    assert (
        RelevadorCalleProvincia.objects.filter(
            profile=user.profile,
            provincia=provincia,
        ).exists()
        is True
    )
    # Flag simple: el relevador es un usuario normal, no un mobile-only.
    assert user.check_password("Sisoc12345!") is True


@pytest.mark.django_db
def test_user_creation_form_relevador_calle_requires_provincia():
    form = UserCreationForm(
        data={
            "username": "relevador_sin_prov",
            "email": "relevador_sin_prov@example.com",
            "password": "Sisoc12345!",
            "tipo_usuario": "interno",
            "es_relevador_calle": True,
            "datacalle_rol": "entrevistador",
        }
    )

    assert form.is_valid() is False
    assert "provincias_datacalle" in form.errors


@pytest.mark.django_db
def test_user_creation_form_relevador_calle_requiere_rol():
    provincia = Provincia.objects.create(nombre="DataCalle Sin Rol Prov")
    form = UserCreationForm(
        data={
            "username": "relevador_sin_rol",
            "email": "relevador_sin_rol@example.com",
            "password": "Sisoc12345!",
            "tipo_usuario": "interno",
            "es_relevador_calle": True,
            "provincias_datacalle": [provincia.id],
        }
    )

    assert form.is_valid() is False
    assert "datacalle_rol" in form.errors


@pytest.mark.django_db
def test_user_creation_form_relevador_calle_excluye_territorial():
    provincia = Provincia.objects.create(nombre="DataCalle Y Comedor Prov")
    form = UserCreationForm(
        data={
            "username": "relevador_y_territorial",
            "email": "relevador_y_territorial@example.com",
            "password": "Sisoc12345!",
            "tipo_usuario": "interno",
            "es_territorial_comedor": True,
            "provincias_territorial": [provincia.id],
            "es_relevador_calle": True,
            "datacalle_rol": "entrevistador",
            "provincias_datacalle": [provincia.id],
        }
    )

    assert form.is_valid() is False
    assert "es_relevador_calle" in form.errors


@pytest.mark.django_db
def test_user_creation_form_relevador_calle_excluye_representante(comedor):
    form = UserCreationForm(
        data={
            "username": "relevador_y_rep",
            "email": "relevador_y_rep@example.com",
            "es_representante_pwa": True,
            "comedores_pwa": [comedor.id],
            "es_relevador_calle": True,
            "datacalle_rol": "entrevistador",
            "provincias_datacalle": [comedor.provincia_id],
        }
    )

    assert form.is_valid() is False
    assert "es_relevador_calle" in form.errors


@pytest.mark.django_db
def test_user_creation_form_relevador_calle_no_entra_al_backoffice():
    provincia = Provincia.objects.create(nombre="DataCalle Backoffice Prov")
    form = UserCreationForm(
        data={
            "username": "relevador_backoffice",
            "email": "relevador_backoffice@example.com",
            "password": "Sisoc12345!",
            "tipo_usuario": "interno",
            "es_relevador_calle": True,
            "datacalle_rol": "entrevistador",
            "provincias_datacalle": [provincia.id],
        }
    )
    assert form.is_valid(), form.errors
    user = form.save()

    assert user.is_staff is False

    login_form = BackofficeAuthenticationForm(
        data={"username": "relevador_backoffice", "password": "Sisoc12345!"}
    )

    assert login_form.is_valid() is False
    assert "solo puede ingresar desde SISOC - Mobile DataCalle" in str(
        login_form.errors
    )


@pytest.mark.django_db
def test_custom_user_change_form_disables_relevador_calle_clears_provincias():
    provincia = Provincia.objects.create(nombre="DataCalle Edit Prov")
    create_form = UserCreationForm(
        data={
            "username": "relevador_edit",
            "email": "relevador_edit@example.com",
            "password": "Sisoc12345!",
            "tipo_usuario": "interno",
            "es_relevador_calle": True,
            "datacalle_rol": "entrevistador",
            "provincias_datacalle": [provincia.id],
        }
    )
    assert create_form.is_valid(), create_form.errors
    user = create_form.save()

    edit_form = CustomUserChangeForm(
        instance=user,
        data={
            "username": user.username,
            "email": user.email,
            "password": "",
            "tipo_usuario": "interno",
            "es_relevador_calle": False,
        },
    )
    assert edit_form.is_valid(), edit_form.errors
    edit_form.save()

    user.profile.refresh_from_db()
    assert user.profile.es_relevador_calle is False
    assert (
        RelevadorCalleProvincia.objects.filter(profile=user.profile).exists() is False
    )


@pytest.mark.django_db
def test_custom_user_change_form_precarga_provincias_datacalle():
    provincia = Provincia.objects.create(nombre="DataCalle Initial Prov")
    create_form = UserCreationForm(
        data={
            "username": "relevador_initial",
            "email": "relevador_initial@example.com",
            "password": "Sisoc12345!",
            "tipo_usuario": "interno",
            "es_relevador_calle": True,
            "datacalle_rol": "entrevistador",
            "provincias_datacalle": [provincia.id],
        }
    )
    assert create_form.is_valid(), create_form.errors
    user = create_form.save()

    edit_form = CustomUserChangeForm(instance=user)

    assert edit_form.fields["es_relevador_calle"].initial is True
    assert edit_form.fields["provincias_datacalle"].initial == [provincia.id]
