import pytest
from django.contrib.auth.models import Group

from comedores.models import Comedor
from core.models import Provincia
from users.forms import (
    BackofficeAuthenticationForm,
    CustomUserChangeForm,
    UserCreationForm,
)
from users.models import AccesoComedorPWA


@pytest.fixture
def comedor(db):
    provincia = Provincia.objects.create(nombre="Mendoza")
    return Comedor.objects.create(nombre="Comedor Forms", provincia=provincia)


@pytest.mark.django_db
def test_user_creation_form_requires_comedor_for_representante():
    form = UserCreationForm(
        data={
            "username": "rep_forms",
            "email": "rep_forms@example.com",
            "password": "Secreta123!",
            "es_representante_pwa": True,
        }
    )

    assert form.is_valid() is False
    assert "comedores_pwa" in form.errors


@pytest.mark.django_db
def test_user_creation_form_creates_representante_with_pwa_access(comedor):
    Group.objects.create(name="Usuario Ver")
    form = UserCreationForm(
        data={
            "username": "rep_forms_ok",
            "email": "rep_forms_ok@example.com",
            "password": "Secreta123!",
            "groups": [],
            "es_representante_pwa": True,
            "comedores_pwa": [comedor.id],
        }
    )

    assert form.is_valid(), form.errors
    user = form.save()

    assert user.is_staff is False
    assert user.groups.count() == 0
    assert (
        AccesoComedorPWA.objects.filter(
            user=user,
            comedor=comedor,
            rol=AccesoComedorPWA.ROL_REPRESENTANTE,
            activo=True,
        ).exists()
        is True
    )


@pytest.mark.django_db
def test_custom_user_change_form_deactivates_representante_access(comedor):
    create_form = UserCreationForm(
        data={
            "username": "rep_edit",
            "email": "rep_edit@example.com",
            "password": "Secreta123!",
            "es_representante_pwa": True,
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


@pytest.mark.django_db
def test_backoffice_authentication_form_rejects_pwa_user(comedor):
    create_form = UserCreationForm(
        data={
            "username": "rep_login_form",
            "email": "rep_login_form@example.com",
            "password": "Secreta123!",
            "es_representante_pwa": True,
            "comedores_pwa": [comedor.id],
        }
    )
    assert create_form.is_valid(), create_form.errors
    create_form.save()

    login_form = BackofficeAuthenticationForm(
        request=None,
        data={"username": "rep_login_form", "password": "Secreta123!"},
    )

    assert login_form.is_valid() is False
    assert "solo puede ingresar desde la PWA" in str(login_form.errors)
