import pytest
from django.contrib.auth.models import User

from centrodeinfancia.forms import CentroDeInfanciaForm
from core.models import Provincia
from users.models import Profile


@pytest.mark.django_db
def test_form_creacion_bloquea_provincia_si_usuario_tiene_provincia():
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    user = User.objects.create_user(username="user-provincia", password="test1234")

    profile, _ = Profile.objects.get_or_create(user=user)
    profile.provincia = provincia
    profile.save()

    form = CentroDeInfanciaForm(
        data={"nombre": "CDI Norte"},
        user=user,
        lock_provincia_from_user=True,
    )

    assert form.fields["provincia"].disabled is True
    assert form.fields["provincia"].initial == provincia
    assert form.is_valid() is True
    assert form.cleaned_data["provincia"] == provincia


@pytest.mark.django_db
def test_form_creacion_no_bloquea_provincia_si_usuario_no_tiene_provincia():
    user = User.objects.create_user(username="user-sin-provincia", password="test1234")

    profile, _ = Profile.objects.get_or_create(user=user)
    profile.provincia = None
    profile.save()

    form = CentroDeInfanciaForm(
        data={"nombre": "CDI Sur"},
        user=user,
        lock_provincia_from_user=True,
    )

    assert form.fields["provincia"].disabled is False
    assert form.is_valid() is True
    assert form.cleaned_data["provincia"] is None


@pytest.mark.django_db
def test_form_includes_apellido_referente_opcional():
    user = User.objects.create_user(username="user-apellido", password="test1234")
    form = CentroDeInfanciaForm(
        data={"nombre": "CDI Este", "apellido_referente": "Gómez"},
        user=user,
        lock_provincia_from_user=False,
    )
    assert "apellido_referente" in form.fields
    assert form.is_valid() is True
    assert form.cleaned_data["apellido_referente"] == "Gómez"
