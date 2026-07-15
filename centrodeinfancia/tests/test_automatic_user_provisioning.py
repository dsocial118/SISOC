import pytest
from django.contrib.auth.models import Group, Permission, User
from django.contrib.messages import get_messages
from django.urls import reverse

from centrodeinfancia.models import AccesoCDI, CentroDeInfancia
from core.constants import UserGroups


def _actor(*, can_delegate=True):
    user = User.objects.create_user(
        username="actor-cdi-automatico",
        email="actor@example.com",
        password="test1234",
    )
    user.user_permissions.add(
        Permission.objects.get(codename="change_centrodeinfancia")
    )
    if can_delegate:
        egp, _ = Group.objects.get_or_create(name=UserGroups.SIMEPI_EGP)
        Group.objects.get_or_create(name=UserGroups.CDI_REFERENTE_CENTRO)
        user.groups.add(egp)
    return user


def _guardar_centro(client, centro, **referente):
    return client.post(
        reverse("centrodeinfancia_editar", kwargs={"pk": centro.pk}),
        {
            "nombre": centro.nombre,
            "telefono": centro.telefono,
            "telefono_referente": centro.telefono_referente,
            **referente,
        },
    )


@pytest.fixture(autouse=True)
def _no_enviar_credenciales(monkeypatch):
    monkeypatch.setattr(
        "users.services_generate_user._enviar_credenciales", lambda **kwargs: False
    )


@pytest.mark.django_db
def test_guardar_cdi_crea_referente_automaticamente(client):
    actor = _actor()
    client.force_login(actor)
    centro = CentroDeInfancia.objects.create(
        nombre="CDI Alta referente",
        telefono="1122334455",
        telefono_referente="1199887766",
    )

    response = _guardar_centro(
        client,
        centro,
        nombre_referente="Lia",
        apellido_referente="Paz",
        email_referente="lia.paz@example.com",
    )

    assert response.status_code == 302
    acceso = AccesoCDI.objects.get(centro=centro)
    assert acceso.user.email == "lia.paz@example.com"
    assert acceso.user.groups.filter(name=UserGroups.CDI_REFERENTE_CENTRO).exists()
    assert acceso.creado_por == actor


@pytest.mark.django_db
def test_reguardar_cdi_no_duplica_referente(client):
    actor = _actor()
    client.force_login(actor)
    centro = CentroDeInfancia.objects.create(
        nombre="CDI Idempotente",
        telefono="1122334455",
        telefono_referente="1199887766",
    )
    referente = {
        "nombre_referente": "Lia",
        "apellido_referente": "Paz",
        "email_referente": "lia.idempotente@example.com",
    }

    _guardar_centro(client, centro, **referente)
    _guardar_centro(client, centro, **referente)

    assert AccesoCDI.objects.filter(centro=centro).count() == 1
    assert User.objects.filter(email="lia.idempotente@example.com").count() == 1


@pytest.mark.django_db
def test_guardar_cdi_sin_email_no_crea_referente_y_avisa(client):
    actor = _actor()
    client.force_login(actor)
    centro = CentroDeInfancia.objects.create(
        nombre="CDI Sin email",
        telefono="1122334455",
        telefono_referente="1199887766",
    )

    response = _guardar_centro(
        client,
        centro,
        nombre_referente="Lia",
        apellido_referente="Paz",
        email_referente="",
    )

    assert response.status_code == 302
    assert not AccesoCDI.objects.filter(centro=centro).exists()
    assert any("falta el email" in str(message) for message in get_messages(response.wsgi_request))


@pytest.mark.django_db
def test_actor_sin_delegacion_guarda_cdi_sin_crear_referente(client):
    actor = _actor(can_delegate=False)
    client.force_login(actor)
    centro = CentroDeInfancia.objects.create(
        nombre="CDI Sin delegacion",
        telefono="1122334455",
        telefono_referente="1199887766",
    )

    response = _guardar_centro(
        client,
        centro,
        nombre_referente="Lia",
        apellido_referente="Paz",
        email_referente="lia.sin-delegacion@example.com",
    )

    centro.refresh_from_db()
    assert response.status_code == 302
    assert centro.email_referente == "lia.sin-delegacion@example.com"
    assert not AccesoCDI.objects.filter(centro=centro).exists()
    assert any(
        "no se pudo crear el referente" in str(message)
        for message in get_messages(response.wsgi_request)
    )
