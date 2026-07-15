import pytest
from django.contrib.auth.models import Group, Permission, User
from django.contrib.messages import get_messages
from django.urls import reverse

from centrodeinfancia.models import AccesoCDI, CentroDeInfancia, Trabajador
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


def _referente_actor(centro):
    user = User.objects.create_user(
        username="referente-cdi-automatico",
        email="referente@example.com",
        password="test1234",
    )
    user.user_permissions.add(
        Permission.objects.get(codename="change_centrodeinfancia")
    )
    referente, _ = Group.objects.get_or_create(name=UserGroups.CDI_REFERENTE_CENTRO)
    Group.objects.get_or_create(name=UserGroups.CDI_TRABAJADOR)
    user.groups.add(referente)
    AccesoCDI.objects.create(user=user, centro=centro)
    return user


def _guardar_trabajador(client, centro, trabajador=None, **datos):
    if trabajador is None:
        url = reverse("centrodeinfancia_trabajador_crear", kwargs={"pk": centro.pk})
    else:
        url = reverse(
            "centrodeinfancia_trabajador_editar",
            kwargs={"pk": centro.pk, "trabajador_id": trabajador.pk},
        )
    return client.post(url, {"nombre": "Ana", "apellido": "Lopez", **datos})


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


@pytest.mark.django_db
def test_guardar_trabajador_con_email_crea_usuario_y_vinculo(client):
    centro = CentroDeInfancia.objects.create(nombre="CDI Trabajadores")
    actor = _referente_actor(centro)
    client.force_login(actor)

    response = _guardar_trabajador(client, centro, email="ana.lopez@example.com")

    assert response.status_code == 302
    trabajador = Trabajador.objects.get(centro=centro)
    assert trabajador.usuario.email == "ana.lopez@example.com"
    assert trabajador.usuario.groups.filter(name=UserGroups.CDI_TRABAJADOR).exists()
    assert not AccesoCDI.objects.filter(user=trabajador.usuario).exists()


@pytest.mark.django_db
def test_guardar_trabajador_sin_email_omite_usuario(client):
    centro = CentroDeInfancia.objects.create(nombre="CDI Trabajadores sin email")
    actor = _referente_actor(centro)
    client.force_login(actor)

    response = _guardar_trabajador(client, centro)

    assert response.status_code == 302
    assert Trabajador.objects.get(centro=centro).usuario is None


@pytest.mark.django_db
def test_reguardar_trabajador_no_duplica_usuario(client):
    centro = CentroDeInfancia.objects.create(nombre="CDI Trabajador idempotente")
    actor = _referente_actor(centro)
    client.force_login(actor)
    _guardar_trabajador(client, centro, email="ana.idempotente@example.com")
    trabajador = Trabajador.objects.get(centro=centro)
    usuario_id = trabajador.usuario_id

    response = _guardar_trabajador(
        client,
        centro,
        trabajador=trabajador,
        email="ana.idempotente@example.com",
    )

    trabajador.refresh_from_db()
    assert response.status_code == 302
    assert trabajador.usuario_id == usuario_id
    assert User.objects.filter(email="ana.idempotente@example.com").count() == 1
