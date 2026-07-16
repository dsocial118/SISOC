import pytest
from django.contrib.auth.models import Group, Permission, User
from django.contrib.messages import get_messages
from django.urls import reverse

from centrodeinfancia.models import AccesoCDI, CentroDeInfancia, Trabajador
from core.constants import UserGroups
from users.models import Profile
from users.services_group_permissions import sync_permissions_for_group


def _actor(*, can_delegate=True):
    user = User.objects.create_user(
        username="actor-cdi-automatico",
        email="actor@example.com",
        password="test1234",
    )
    user.user_permissions.add(
        Permission.objects.get(codename="add_centrodeinfancia"),
        Permission.objects.get(codename="change_centrodeinfancia"),
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
    referente, _ = Group.objects.get_or_create(name=UserGroups.CDI_REFERENTE_CENTRO)
    sync_permissions_for_group(referente)
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


def _usuario_temporal(username, email, *, must_change_password):
    user = User.objects.create_user(username=username, email=email, password="test1234")
    profile, _ = Profile.objects.get_or_create(user=user)
    profile.must_change_password = must_change_password
    profile.save(update_fields=["must_change_password"])
    return user


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
def test_crear_cdi_con_referente_crea_usuario_automaticamente(client):
    actor = _actor()
    client.force_login(actor)

    response = client.post(
        reverse("centrodeinfancia_crear"),
        {
            "nombre": "CDI Alta completa",
            "telefono": "1122334455",
            "telefono_referente": "1199887766",
            "nombre_referente": "Lia",
            "apellido_referente": "Paz",
            "email_referente": "lia.alta@example.com",
        },
    )

    assert response.status_code == 302
    centro = CentroDeInfancia.objects.get(nombre="CDI Alta completa")
    assert AccesoCDI.objects.get(centro=centro).user.email == "lia.alta@example.com"


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
    assert any(
        "falta el email" in str(message)
        for message in get_messages(response.wsgi_request)
    )


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
def test_trabajadores_con_email_repetido_reciben_usuarios_distintos(client):
    centro = CentroDeInfancia.objects.create(nombre="CDI Trabajadores email repetido")
    actor = _referente_actor(centro)
    client.force_login(actor)

    _guardar_trabajador(client, centro, email="compartido@example.com")
    _guardar_trabajador(client, centro, email="compartido@example.com")

    trabajadores = list(Trabajador.objects.filter(centro=centro))
    assert len(trabajadores) == 2
    assert all(trabajador.usuario_id for trabajador in trabajadores)
    assert trabajadores[0].usuario_id != trabajadores[1].usuario_id
    assert User.objects.filter(email="compartido@example.com").count() == 2
    assert len({trabajador.usuario.username for trabajador in trabajadores}) == 2
    assert not AccesoCDI.objects.filter(
        user_id__in=[trabajador.usuario_id for trabajador in trabajadores]
    ).exists()


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


@pytest.mark.django_db
def test_email_referente_se_sincroniza_si_aun_debe_cambiar_password(client):
    actor = _actor()
    client.force_login(actor)
    centro = CentroDeInfancia.objects.create(
        nombre="CDI Sync referente",
        telefono="1122334455",
        telefono_referente="1199887766",
        nombre_referente="Lia",
        apellido_referente="Paz",
        email_referente="anterior.referente@example.com",
    )
    referente = _usuario_temporal(
        "referente-estable",
        "anterior.referente@example.com",
        must_change_password=True,
    )
    AccesoCDI.objects.create(user=referente, centro=centro)

    response = _guardar_centro(
        client,
        centro,
        nombre_referente="Lia",
        apellido_referente="Paz",
        email_referente="nuevo.referente@example.com",
    )

    referente.refresh_from_db()
    assert response.status_code == 302
    assert referente.email == "nuevo.referente@example.com"
    assert referente.username == "referente-estable"


@pytest.mark.django_db
def test_email_referente_no_se_sincroniza_si_el_campo_no_cambio(client):
    actor = _actor()
    client.force_login(actor)
    centro = CentroDeInfancia.objects.create(
        nombre="CDI Sync referente sin cambio",
        telefono="1122334455",
        telefono_referente="1199887766",
        nombre_referente="Lia",
        apellido_referente="Paz",
        email_referente="email.cdi@example.com",
    )
    referente = _usuario_temporal(
        "referente-sin-cambio",
        "email.cuenta@example.com",
        must_change_password=True,
    )
    AccesoCDI.objects.create(user=referente, centro=centro)

    response = _guardar_centro(
        client,
        centro,
        nombre_referente="Lia",
        apellido_referente="Paz",
        email_referente="email.cdi@example.com",
    )

    referente.refresh_from_db()
    assert response.status_code == 302
    assert referente.email == "email.cuenta@example.com"


@pytest.mark.django_db
def test_email_referente_se_limpia_si_el_campo_cambio_a_vacio(client):
    actor = _actor()
    client.force_login(actor)
    centro = CentroDeInfancia.objects.create(
        nombre="CDI Sync referente vacío",
        telefono="1122334455",
        telefono_referente="1199887766",
        nombre_referente="Lia",
        apellido_referente="Paz",
        email_referente="referente.a.limpiar@example.com",
    )
    referente = _usuario_temporal(
        "referente-limpiar-email",
        "referente.a.limpiar@example.com",
        must_change_password=True,
    )
    AccesoCDI.objects.create(user=referente, centro=centro)

    response = _guardar_centro(
        client,
        centro,
        nombre_referente="Lia",
        apellido_referente="Paz",
        email_referente="",
    )

    referente.refresh_from_db()
    assert response.status_code == 302
    assert referente.email == ""
    assert referente.username == "referente-limpiar-email"


@pytest.mark.django_db
def test_email_referente_no_se_sincroniza_si_ya_modifico_cuenta(client):
    actor = _actor()
    client.force_login(actor)
    centro = CentroDeInfancia.objects.create(
        nombre="CDI Sync referente protegido",
        telefono="1122334455",
        telefono_referente="1199887766",
        nombre_referente="Lia",
        apellido_referente="Paz",
        email_referente="anterior.protegido@example.com",
    )
    referente = _usuario_temporal(
        "referente-protegido",
        "anterior.protegido@example.com",
        must_change_password=False,
    )
    AccesoCDI.objects.create(user=referente, centro=centro)

    response = _guardar_centro(
        client,
        centro,
        nombre_referente="Lia",
        apellido_referente="Paz",
        email_referente="nuevo.protegido@example.com",
    )

    referente.refresh_from_db()
    assert referente.email == "anterior.protegido@example.com"
    assert referente.username == "referente-protegido"
    assert any(
        "ya modificó su cuenta" in str(message)
        for message in get_messages(response.wsgi_request)
    )


@pytest.mark.django_db
def test_email_referente_se_sincroniza_con_el_acceso_del_email_anterior(client):
    actor = _actor()
    client.force_login(actor)
    centro = CentroDeInfancia.objects.create(
        nombre="CDI Sync referente multiple",
        telefono="1122334455",
        telefono_referente="1199887766",
        nombre_referente="Lia",
        apellido_referente="Paz",
        email_referente="referente.original@example.com",
    )
    acceso_ajeno = _usuario_temporal(
        "acceso-ajeno-estable",
        "acceso.ajeno@example.com",
        must_change_password=True,
    )
    referente = _usuario_temporal(
        "referente-correcto-estable",
        "referente.original@example.com",
        must_change_password=True,
    )
    AccesoCDI.objects.create(user=acceso_ajeno, centro=centro)
    AccesoCDI.objects.create(user=referente, centro=centro)

    response = _guardar_centro(
        client,
        centro,
        nombre_referente="Lia",
        apellido_referente="Paz",
        email_referente="referente.nuevo@example.com",
    )

    referente.refresh_from_db()
    acceso_ajeno.refresh_from_db()
    assert response.status_code == 302
    assert referente.email == "referente.nuevo@example.com"
    assert referente.username == "referente-correcto-estable"
    assert acceso_ajeno.email == "acceso.ajeno@example.com"


@pytest.mark.django_db
def test_email_trabajador_se_sincroniza_si_aun_debe_cambiar_password(client):
    centro = CentroDeInfancia.objects.create(nombre="CDI Sync trabajador")
    actor = _referente_actor(centro)
    client.force_login(actor)
    usuario = _usuario_temporal(
        "trabajador-estable",
        "anterior.trabajador@example.com",
        must_change_password=True,
    )
    trabajador = Trabajador.objects.create(
        centro=centro,
        usuario=usuario,
        nombre="Ana",
        apellido="Lopez",
        email="anterior.trabajador@example.com",
    )

    response = _guardar_trabajador(
        client,
        centro,
        trabajador=trabajador,
        email="nuevo.trabajador@example.com",
    )

    usuario.refresh_from_db()
    assert response.status_code == 302
    assert usuario.email == "nuevo.trabajador@example.com"
    assert usuario.username == "trabajador-estable"


@pytest.mark.django_db
def test_email_trabajador_no_se_sincroniza_si_el_campo_no_cambio(client):
    centro = CentroDeInfancia.objects.create(nombre="CDI Sync trabajador sin cambio")
    actor = _referente_actor(centro)
    client.force_login(actor)
    usuario = _usuario_temporal(
        "trabajador-sin-cambio",
        "email.cuenta.trabajador@example.com",
        must_change_password=True,
    )
    trabajador = Trabajador.objects.create(
        centro=centro,
        usuario=usuario,
        nombre="Ana",
        apellido="Lopez",
        email="email.ficha.trabajador@example.com",
    )

    response = _guardar_trabajador(
        client,
        centro,
        trabajador=trabajador,
        email="email.ficha.trabajador@example.com",
    )

    usuario.refresh_from_db()
    assert response.status_code == 302
    assert usuario.email == "email.cuenta.trabajador@example.com"


@pytest.mark.django_db
def test_email_trabajador_se_limpia_si_el_campo_cambio_a_vacio(client):
    centro = CentroDeInfancia.objects.create(nombre="CDI Sync trabajador vacío")
    actor = _referente_actor(centro)
    client.force_login(actor)
    usuario = _usuario_temporal(
        "trabajador-limpiar-email",
        "trabajador.a.limpiar@example.com",
        must_change_password=True,
    )
    trabajador = Trabajador.objects.create(
        centro=centro,
        usuario=usuario,
        nombre="Ana",
        apellido="Lopez",
        email="trabajador.a.limpiar@example.com",
    )

    response = _guardar_trabajador(
        client,
        centro,
        trabajador=trabajador,
        email="",
    )

    usuario.refresh_from_db()
    assert response.status_code == 302
    assert usuario.email == ""
    assert usuario.username == "trabajador-limpiar-email"


@pytest.mark.django_db
def test_email_trabajador_no_se_sincroniza_si_ya_modifico_cuenta(client):
    centro = CentroDeInfancia.objects.create(nombre="CDI Sync trabajador protegido")
    actor = _referente_actor(centro)
    client.force_login(actor)
    usuario = _usuario_temporal(
        "trabajador-protegido",
        "anterior.trabajador.protegido@example.com",
        must_change_password=False,
    )
    trabajador = Trabajador.objects.create(
        centro=centro,
        usuario=usuario,
        nombre="Ana",
        apellido="Lopez",
        email="anterior.trabajador.protegido@example.com",
    )

    response = _guardar_trabajador(
        client,
        centro,
        trabajador=trabajador,
        email="nuevo.trabajador.protegido@example.com",
    )

    usuario.refresh_from_db()
    assert usuario.email == "anterior.trabajador.protegido@example.com"
    assert usuario.username == "trabajador-protegido"
    assert any(
        "ya modificó su cuenta" in str(message)
        for message in get_messages(response.wsgi_request)
    )
