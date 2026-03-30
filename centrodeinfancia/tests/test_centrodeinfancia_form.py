import pytest
from django.contrib.auth.models import User

from centrodeinfancia.forms import CentroDeInfanciaForm
from centrodeinfancia.models import CentroDeInfancia
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


@pytest.mark.django_db
def test_form_acepta_numero_calle_opcional():
    user = User.objects.create_user(username="user-numero", password="test1234")
    form = CentroDeInfanciaForm(
        data={
            "nombre": "CDI Norte",
            "calle": "San Martín",
            "numero": "123",
        },
        user=user,
        lock_provincia_from_user=False,
    )

    assert "numero" in form.fields
    assert form.is_valid()
    assert form.cleaned_data["numero"] == "123"


@pytest.mark.django_db
def test_form_rechaza_texto_en_campos_numericos():
    user = User.objects.create_user(
        username="user-campos-numericos",
        password="test1234",
    )
    form = CentroDeInfanciaForm(
        data={
            "nombre": "CDI Texto",
            "numero": "12A",
            "telefono": "11-ABCD-1234",
            "telefono_referente": "abc",
        },
        user=user,
        lock_provincia_from_user=False,
    )

    assert not form.is_valid()
    assert "numero" in form.errors
    assert "telefono" in form.errors
    assert "telefono_referente" in form.errors


@pytest.mark.django_db
def test_form_acepta_telefono_como_numero_plano():
    user = User.objects.create_user(
        username="user-telefono-plano",
        password="test1234",
    )
    form = CentroDeInfanciaForm(
        data={
            "nombre": "CDI Teléfono",
            "telefono": "5491140333588",
            "telefono_referente": "1133557799",
        },
        user=user,
        lock_provincia_from_user=False,
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["telefono"] == "5491140333588"
    assert form.cleaned_data["telefono_referente"] == "1133557799"


@pytest.mark.django_db
def test_form_acepta_telefono_con_guiones_opcionales():
    user = User.objects.create_user(
        username="user-telefono-guiones",
        password="test1234",
    )
    form = CentroDeInfanciaForm(
        data={
            "nombre": "CDI Teléfono Guiones",
            "telefono": "11-1234-1234",
            "telefono_referente": "549-11-4033-3588",
        },
        user=user,
        lock_provincia_from_user=False,
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["telefono"] == "11-1234-1234"
    assert form.cleaned_data["telefono_referente"] == "549-11-4033-3588"


@pytest.mark.django_db
def test_form_edicion_mantiene_campos_obligatorios():
    user = User.objects.create_user(
        username="user-edicion-obligatorios",
        password="test1234",
    )
    centro = CentroDeInfancia.objects.create(nombre="CDI Inicial")

    form = CentroDeInfanciaForm(
        data={"nombre": ""},
        instance=centro,
        user=user,
        lock_provincia_from_user=False,
    )

    assert not form.is_valid()
    assert "nombre" in form.errors
