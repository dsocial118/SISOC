"""Tests for test users pwa forms."""

import pytest
from django.contrib.auth.models import Group, Permission

from comedores.models import Comedor
from core.models import Provincia
from organizaciones.models import Organizacion
from users.forms import (
    BackofficeAuthenticationForm,
    CustomUserChangeForm,
    UserCreationForm,
)
from users.models import AccesoComedorPWA, AuditAccesoComedorPWA

MOBILE_RENDICION_PERMISSION_CODE = "rendicioncuentasmensual.manage_mobile_rendicion"


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
            "email": "rep_forms@example.com",
            "es_representante_pwa": True,
        }
    )

    assert form.is_valid() is False
    assert "comedores_pwa" in form.errors


@pytest.mark.django_db
def test_user_creation_form_requires_visible_space_for_mobile_user(comedor):
    form = UserCreationForm(
        data={
            "username": "rep_forms_org",
            "email": "rep_forms_org@example.com",
            "es_representante_pwa": True,
            "tipo_asociacion_pwa": AccesoComedorPWA.TIPO_ASOCIACION_ORGANIZACION,
            "organizaciones_pwa": [comedor.organizacion_id],
        }
    )

    assert form.is_valid() is False
    assert "comedores_pwa" in form.errors


@pytest.mark.django_db
def test_user_creation_form_creates_mobile_user_associated_to_organization(comedor):
    Group.objects.create(name="Usuario Ver")
    form = UserCreationForm(
        data={
            "username": "rep_forms_ok",
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
def test_user_creation_form_assigns_mobile_rendicion_permission_with_checkbox(comedor):
    form = UserCreationForm(
        data={
            "username": "rep_forms_rendicion",
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
def test_custom_user_change_form_can_remove_mobile_rendicion_permission(comedor):
    permission = Permission.objects.get(
        content_type__app_label="rendicioncuentasmensual",
        codename="manage_mobile_rendicion",
    )
    create_form = UserCreationForm(
        data={
            "username": "rep_edit_rendicion",
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
def test_user_creation_form_allows_some_spaces_from_org_plus_external_space(
    comedor, comedor_mismo_org, comedor_extra
):
    form = UserCreationForm(
        data={
            "username": "rep_forms_partial_org",
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
            activo=True,
        ).exists()
        is False
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
def test_backoffice_authentication_form_rejects_mobile_user(comedor):
    create_form = UserCreationForm(
        data={
            "username": "rep_login_form",
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
            "password": create_form.generated_password,
        },
    )

    assert login_form.is_valid() is False
    assert "solo puede ingresar desde la PWA" in str(login_form.errors)
