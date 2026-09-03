"""Tests for test users pwa forms."""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission

from comedores.models import Comedor
from core.models import Provincia
from duplas.models import Dupla
from organizaciones.models import Organizacion
from users.forms import (
    BackofficeAuthenticationForm,
    CustomUserChangeForm,
    UserCreationForm,
)
from users.models import (
    AccesoComedorPWA,
    AccesoOrganizacionPWA,
    AuditAccesoComedorPWA,
    CoordinadorEquipoTecnicoPWA,
    TerritorialComedorProvincia,
)
from users.services_pwa import get_access_rows

MOBILE_RENDICION_PERMISSION_CODE = "rendicioncuentasmensual.manage_mobile_rendicion"


def test_user_creation_form_provincia_usa_select2():
    field = UserCreationForm.base_fields["provincia"]

    assert "select2" in field.widget.attrs["class"].split()


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
