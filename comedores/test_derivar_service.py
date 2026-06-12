import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import Client
from django.urls import reverse

from admisiones.models.admisiones import Admision
from ciudadanos.models import Ciudadano
from comedores.models import Comedor, Nomina, NominaDerivacion, Programas
from comedores.services.comedor_service import ComedorService

User = get_user_model()


def _make_programa(usa_admision=False):
    return Programas.objects.create(
        nombre="Prog test", usa_admision_para_nomina=usa_admision
    )


def _make_ciudadano(doc=11111111):
    return Ciudadano.objects.create(
        apellido="Derivar",
        nombre="Test",
        documento=doc,
    )


def _make_user(username="derivar_user"):
    return User.objects.create_superuser(
        username=username, email=f"{username}@test.com", password="testpass"
    )


@pytest.mark.django_db
def test_transferir_camino_feliz_directo():
    programa = _make_programa(usa_admision=False)
    comedor_origen = Comedor.objects.create(nombre="Origen", programa=programa)
    comedor_destino = Comedor.objects.create(nombre="Destino", programa=programa)
    ciudadano = _make_ciudadano()
    nomina = Nomina.objects.create(
        ciudadano=ciudadano,
        comedor=comedor_origen,
        estado=Nomina.ESTADO_ACTIVO,
    )
    usuario = _make_user()

    ok, msg = ComedorService.transferir_ciudadano_entre_centros(
        nomina_pk=nomina.pk,
        comedor_destino_pk=comedor_destino.pk,
        usuario=usuario,
    )

    assert ok is True
    nomina.refresh_from_db()
    assert nomina.estado == Nomina.ESTADO_BAJA
    nomina_destino = Nomina.objects.get(
        ciudadano=ciudadano, comedor=comedor_destino, admision__isnull=True
    )
    assert nomina_destino.estado == Nomina.ESTADO_ESPERA
    assert NominaDerivacion.objects.filter(
        nomina_origen=nomina, nomina_destino=nomina_destino
    ).exists()


@pytest.mark.django_db
def test_transferir_camino_feliz_con_admision():
    programa_sin = _make_programa(usa_admision=False)
    programa_con = _make_programa(usa_admision=True)
    comedor_origen = Comedor.objects.create(nombre="Origen ad", programa=programa_sin)
    comedor_destino = Comedor.objects.create(nombre="Destino ad", programa=programa_con)
    admision_destino = Admision.objects.create(
        comedor=comedor_destino, tipo="incorporacion", activa=True
    )
    ciudadano = _make_ciudadano(doc=22222222)
    nomina = Nomina.objects.create(
        ciudadano=ciudadano,
        comedor=comedor_origen,
        estado=Nomina.ESTADO_ACTIVO,
    )
    usuario = _make_user("derivar_user2")

    ok, msg = ComedorService.transferir_ciudadano_entre_centros(
        nomina_pk=nomina.pk,
        comedor_destino_pk=comedor_destino.pk,
        usuario=usuario,
    )

    assert ok is True
    nomina.refresh_from_db()
    assert nomina.estado == Nomina.ESTADO_BAJA
    nomina_destino = Nomina.objects.get(ciudadano=ciudadano, admision=admision_destino)
    assert nomina_destino.estado == Nomina.ESTADO_ESPERA
    assert NominaDerivacion.objects.filter(
        nomina_origen=nomina, nomina_destino=nomina_destino
    ).exists()


@pytest.mark.django_db
def test_transferir_falla_estado_no_activo():
    programa = _make_programa(usa_admision=False)
    comedor_origen = Comedor.objects.create(nombre="Origen ea", programa=programa)
    comedor_destino = Comedor.objects.create(nombre="Destino ea", programa=programa)
    ciudadano = _make_ciudadano(doc=33333333)
    nomina = Nomina.objects.create(
        ciudadano=ciudadano,
        comedor=comedor_origen,
        estado=Nomina.ESTADO_BAJA,
    )
    usuario = _make_user("derivar_user3")

    ok, msg = ComedorService.transferir_ciudadano_entre_centros(
        nomina_pk=nomina.pk,
        comedor_destino_pk=comedor_destino.pk,
        usuario=usuario,
    )

    assert ok is False
    assert "Activo" in msg


@pytest.mark.django_db
def test_transferir_falla_destino_igual_a_origen():
    programa = _make_programa(usa_admision=False)
    comedor = Comedor.objects.create(nombre="Unico", programa=programa)
    ciudadano = _make_ciudadano(doc=44444444)
    nomina = Nomina.objects.create(
        ciudadano=ciudadano,
        comedor=comedor,
        estado=Nomina.ESTADO_ACTIVO,
    )
    usuario = _make_user("derivar_user4")

    ok, msg = ComedorService.transferir_ciudadano_entre_centros(
        nomina_pk=nomina.pk,
        comedor_destino_pk=comedor.pk,
        usuario=usuario,
    )

    assert ok is False
    assert "diferente" in msg.lower()


@pytest.mark.django_db
def test_transferir_falla_persona_ya_existe_en_destino():
    programa = _make_programa(usa_admision=False)
    comedor_origen = Comedor.objects.create(nombre="Origen dup", programa=programa)
    comedor_destino = Comedor.objects.create(nombre="Destino dup", programa=programa)
    ciudadano = _make_ciudadano(doc=55555555)
    nomina = Nomina.objects.create(
        ciudadano=ciudadano,
        comedor=comedor_origen,
        estado=Nomina.ESTADO_ACTIVO,
    )
    Nomina.objects.create(
        ciudadano=ciudadano,
        comedor=comedor_destino,
        estado=Nomina.ESTADO_ACTIVO,
    )
    usuario = _make_user("derivar_user5")

    ok, msg = ComedorService.transferir_ciudadano_entre_centros(
        nomina_pk=nomina.pk,
        comedor_destino_pk=comedor_destino.pk,
        usuario=usuario,
    )

    assert ok is False
    assert "ya tiene" in msg.lower()


@pytest.mark.django_db
def test_transferir_falla_admision_destino_sin_admision_activa():
    programa_sin = _make_programa(usa_admision=False)
    programa_con = _make_programa(usa_admision=True)
    comedor_origen = Comedor.objects.create(nombre="Origen na", programa=programa_sin)
    comedor_destino = Comedor.objects.create(nombre="Destino na", programa=programa_con)
    ciudadano = _make_ciudadano(doc=66666666)
    nomina = Nomina.objects.create(
        ciudadano=ciudadano,
        comedor=comedor_origen,
        estado=Nomina.ESTADO_ACTIVO,
    )
    usuario = _make_user("derivar_user6")

    ok, msg = ComedorService.transferir_ciudadano_entre_centros(
        nomina_pk=nomina.pk,
        comedor_destino_pk=comedor_destino.pk,
        usuario=usuario,
    )

    assert ok is False
    assert "admisión activa" in msg.lower()


@pytest.mark.django_db
def test_nomina_derivar_view_get_returns_405(client):
    user = _make_user("derivar_view_get")
    client.force_login(user)
    programa = _make_programa(usa_admision=False)
    comedor = Comedor.objects.create(nombre="Comedor view", programa=programa)
    ciudadano = _make_ciudadano(doc=77777777)
    nomina = Nomina.objects.create(
        ciudadano=ciudadano, comedor=comedor, estado=Nomina.ESTADO_ACTIVO
    )
    url = reverse("nomina_derivar", kwargs={"pk": nomina.pk})

    response = client.get(url)

    assert response.status_code == 405


@pytest.mark.django_db
def test_nomina_derivar_view_sin_autenticacion(client):
    programa = _make_programa(usa_admision=False)
    comedor = Comedor.objects.create(nombre="Comedor anon", programa=programa)
    ciudadano = _make_ciudadano(doc=88888888)
    nomina = Nomina.objects.create(
        ciudadano=ciudadano, comedor=comedor, estado=Nomina.ESTADO_ACTIVO
    )
    url = reverse("nomina_derivar", kwargs={"pk": nomina.pk})

    response = client.post(url, data={"comedor_destino_id": "1"})

    assert response.status_code in (302, 403)


@pytest.mark.django_db
def test_nomina_derivar_view_centro_destino_invalido(client):
    user = _make_user("derivar_view_inv")
    client.force_login(user)
    programa = _make_programa(usa_admision=False)
    comedor = Comedor.objects.create(nombre="Comedor inv", programa=programa)
    ciudadano = _make_ciudadano(doc=99999999)
    nomina = Nomina.objects.create(
        ciudadano=ciudadano, comedor=comedor, estado=Nomina.ESTADO_ACTIVO
    )
    url = reverse("nomina_derivar", kwargs={"pk": nomina.pk})

    response = client.post(url, data={"comedor_destino_id": "no_es_numero"})

    assert response.status_code == 400


@pytest.mark.django_db
def test_nomina_derivar_view_post_exitoso(client):
    user = _make_user("derivar_view_ok")
    client.force_login(user)
    programa = _make_programa(usa_admision=False)
    comedor_origen = Comedor.objects.create(nombre="Origen view ok", programa=programa)
    comedor_destino = Comedor.objects.create(
        nombre="Destino view ok", programa=programa
    )
    ciudadano = _make_ciudadano(doc=12121212)
    nomina = Nomina.objects.create(
        ciudadano=ciudadano, comedor=comedor_origen, estado=Nomina.ESTADO_ACTIVO
    )
    url = reverse("nomina_derivar", kwargs={"pk": nomina.pk})

    response = client.post(url, data={"comedor_destino_id": str(comedor_destino.pk)})

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
