import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from ciudadanos.models import Ciudadano
from core.models import Provincia
from centrodeinfancia.models import (
    CentroDeInfancia,
    NominaCentroInfancia,
    NominaCentroInfanciaDerivacion,
)
from centrodeinfancia.services import CentroDeInfanciaService

User = get_user_model()


def _make_centro(nombre="CDI Test"):
    return CentroDeInfancia.objects.create(nombre=nombre)


def _make_ciudadano(doc=21111111):
    return Ciudadano.objects.create(
        apellido="Derivar",
        nombre="CDI",
        documento=doc,
    )


def _make_user(username="cdi_derivar_user"):
    return User.objects.create_superuser(
        username=username, email=f"{username}@test.com", password="testpass"
    )


def _make_nomina(centro, ciudadano, estado=NominaCentroInfancia.ESTADO_ACTIVO):
    return NominaCentroInfancia.objects.create(
        centro=centro,
        ciudadano=ciudadano,
        estado=estado,
    )


@pytest.mark.django_db
def test_transferir_camino_feliz():
    centro_origen = _make_centro("CDI Origen")
    centro_destino = _make_centro("CDI Destino")
    ciudadano = _make_ciudadano()
    nomina = _make_nomina(centro_origen, ciudadano)
    usuario = _make_user()

    ok, msg = CentroDeInfanciaService.transferir_ciudadano_entre_centros(
        nomina_pk=nomina.pk,
        centro_destino_pk=centro_destino.pk,
        usuario=usuario,
    )

    assert ok is True
    nomina.refresh_from_db()
    assert nomina.estado == NominaCentroInfancia.ESTADO_BAJA
    nomina_destino = NominaCentroInfancia.objects.get(
        ciudadano=ciudadano, centro=centro_destino
    )
    assert nomina_destino.estado == NominaCentroInfancia.ESTADO_PENDIENTE
    derivacion = NominaCentroInfanciaDerivacion.objects.get(
        nomina_origen=nomina, nomina_destino=nomina_destino
    )
    assert derivacion.centro_origen_id == centro_origen.pk
    assert derivacion.centro_destino_id == centro_destino.pk
    assert derivacion.usuario == usuario


@pytest.mark.django_db
def test_transferir_camino_feliz_copia_campos():
    centro_origen = _make_centro("CDI Campos Origen")
    centro_destino = _make_centro("CDI Campos Destino")
    ciudadano = _make_ciudadano(doc=21222222)
    provincia = Provincia.objects.create(nombre="Provincia derivar test")
    nomina = NominaCentroInfancia.objects.create(
        centro=centro_origen,
        ciudadano=ciudadano,
        estado=NominaCentroInfancia.ESTADO_ACTIVO,
        apellido="Derivar",
        nombre="CDI",
        sala="Sala Azul",
        provincia_domicilio=provincia,
    )
    usuario = _make_user("cdi_campos_user")

    ok, _ = CentroDeInfanciaService.transferir_ciudadano_entre_centros(
        nomina_pk=nomina.pk,
        centro_destino_pk=centro_destino.pk,
        usuario=usuario,
    )

    assert ok is True
    nomina_destino = NominaCentroInfancia.objects.get(
        ciudadano=ciudadano, centro=centro_destino
    )
    assert nomina_destino.apellido == "Derivar"
    assert nomina_destino.nombre == "CDI"
    assert nomina_destino.sala == "Sala Azul"
    assert nomina_destino.provincia_domicilio_id == provincia.pk


@pytest.mark.django_db
def test_transferir_falla_estado_no_activo():
    centro_origen = _make_centro("CDI Baja Origen")
    centro_destino = _make_centro("CDI Baja Destino")
    ciudadano = _make_ciudadano(doc=21333333)
    nomina = _make_nomina(
        centro_origen, ciudadano, estado=NominaCentroInfancia.ESTADO_BAJA
    )
    usuario = _make_user("cdi_baja_user")

    ok, msg = CentroDeInfanciaService.transferir_ciudadano_entre_centros(
        nomina_pk=nomina.pk,
        centro_destino_pk=centro_destino.pk,
        usuario=usuario,
    )

    assert ok is False
    assert "Activo" in msg


@pytest.mark.django_db
def test_transferir_falla_destino_igual_a_origen():
    centro = _make_centro("CDI Unico")
    ciudadano = _make_ciudadano(doc=21444444)
    nomina = _make_nomina(centro, ciudadano)
    usuario = _make_user("cdi_unico_user")

    ok, msg = CentroDeInfanciaService.transferir_ciudadano_entre_centros(
        nomina_pk=nomina.pk,
        centro_destino_pk=centro.pk,
        usuario=usuario,
    )

    assert ok is False
    assert "diferente" in msg.lower()


@pytest.mark.django_db
def test_transferir_falla_persona_ya_existe_en_destino_activo():
    centro_origen = _make_centro("CDI Dup Origen")
    centro_destino = _make_centro("CDI Dup Destino")
    ciudadano = _make_ciudadano(doc=21555555)
    nomina = _make_nomina(centro_origen, ciudadano)
    _make_nomina(centro_destino, ciudadano, estado=NominaCentroInfancia.ESTADO_ACTIVO)
    usuario = _make_user("cdi_dup_user")

    ok, msg = CentroDeInfanciaService.transferir_ciudadano_entre_centros(
        nomina_pk=nomina.pk,
        centro_destino_pk=centro_destino.pk,
        usuario=usuario,
    )

    assert ok is False
    assert "ya tiene" in msg.lower()


@pytest.mark.django_db
def test_transferir_falla_persona_ya_existe_en_destino_pendiente():
    centro_origen = _make_centro("CDI Pend Origen")
    centro_destino = _make_centro("CDI Pend Destino")
    ciudadano = _make_ciudadano(doc=21666666)
    nomina = _make_nomina(centro_origen, ciudadano)
    _make_nomina(
        centro_destino, ciudadano, estado=NominaCentroInfancia.ESTADO_PENDIENTE
    )
    usuario = _make_user("cdi_pend_user")

    ok, msg = CentroDeInfanciaService.transferir_ciudadano_entre_centros(
        nomina_pk=nomina.pk,
        centro_destino_pk=centro_destino.pk,
        usuario=usuario,
    )

    assert ok is False
    assert "ya tiene" in msg.lower()


@pytest.mark.django_db
def test_nomina_cdi_derivar_view_get_returns_405(client):
    user = _make_user("cdi_view_get")
    client.force_login(user)
    centro = _make_centro("CDI View GET")
    ciudadano = _make_ciudadano(doc=21777777)
    nomina = _make_nomina(centro, ciudadano)
    url = reverse("centrodeinfancia_nomina_derivar", kwargs={"pk": nomina.pk})

    response = client.get(url)

    assert response.status_code == 405


@pytest.mark.django_db
def test_nomina_cdi_derivar_view_sin_autenticacion(client):
    centro = _make_centro("CDI View Anon")
    ciudadano = _make_ciudadano(doc=21888888)
    nomina = _make_nomina(centro, ciudadano)
    url = reverse("centrodeinfancia_nomina_derivar", kwargs={"pk": nomina.pk})

    response = client.post(url, data={"centro_destino_id": "1"})

    assert response.status_code in (302, 403)


@pytest.mark.django_db
def test_nomina_cdi_derivar_view_centro_destino_invalido(client):
    user = _make_user("cdi_view_inv")
    client.force_login(user)
    centro = _make_centro("CDI View Inv")
    ciudadano = _make_ciudadano(doc=21999999)
    nomina = _make_nomina(centro, ciudadano)
    url = reverse("centrodeinfancia_nomina_derivar", kwargs={"pk": nomina.pk})

    response = client.post(url, data={"centro_destino_id": "no_es_numero"})

    assert response.status_code == 400


@pytest.mark.django_db
def test_nomina_cdi_derivar_view_post_exitoso(client):
    user = _make_user("cdi_view_ok")
    client.force_login(user)
    centro_origen = _make_centro("CDI View Ok Origen")
    centro_destino = _make_centro("CDI View Ok Destino")
    ciudadano = _make_ciudadano(doc=22000000)
    nomina = _make_nomina(centro_origen, ciudadano)
    url = reverse("centrodeinfancia_nomina_derivar", kwargs={"pk": nomina.pk})

    response = client.post(url, data={"centro_destino_id": str(centro_destino.pk)})

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
