"""Tests del autocompletado en cadena (N17).

El detalle territorial del comedor expone ``seguimiento_anterior_mobile``: el
snapshot del seguimiento inmediato anterior al que el territorial va a
completar, con el mismo formato de secciones que ``relevamiento_actual_mobile``.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from comedores.models import Comedor
from core.models import Provincia
from relevamientos.models import (
    PrimerSeguimiento,
    Relevamiento,
    ServiciosBasicosSeguimiento,
)
from users.models import TerritorialComedorProvincia


def _token_client(user):
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


def _escenario(nombre):
    provincia = Provincia.objects.create(nombre=f"Prov {nombre}")
    comedor = Comedor.objects.create(nombre=f"Comedor {nombre}", provincia=provincia)
    user = get_user_model().objects.create_user(
        username=f"terr_{nombre}",
        email=f"terr_{nombre}@example.com",
        password="testpass123",
    )
    user.profile.es_territorial_comedor = True
    user.profile.save(update_fields=["es_territorial_comedor"])
    TerritorialComedorProvincia.objects.create(
        profile=user.profile, provincia=provincia
    )
    relevamiento = Relevamiento.objects.create(
        comedor=comedor, estado="Visita pendiente", territorial_user=user
    )
    return user, comedor, relevamiento


def _instancia(relevamiento, numero_orden, estado, *, tipo=None, agua=None):
    servicios = None
    if agua is not None:
        servicios = ServiciosBasicosSeguimiento.objects.create(
            agua_potable=agua, banio="Dentro del espacio"
        )
    return PrimerSeguimiento.objects.create(
        id_relevamiento=relevamiento,
        numero_orden=numero_orden,
        tipo=tipo or PrimerSeguimiento.TIPO_PRIMER,
        estado=estado,
        servicios_basicos=servicios,
    )


def _detalle(user, comedor):
    return _token_client(user).get(f"/api/territorial/comedores/{comedor.id}/")


@pytest.mark.django_db
def test_sin_seguimientos_el_prefill_es_none():
    user, comedor, _ = _escenario("prefill_vacio")

    response = _detalle(user, comedor)

    assert response.status_code == 200
    assert response.data["seguimiento_anterior_mobile"] is None


@pytest.mark.django_db
def test_con_una_sola_instancia_pendiente_no_hay_anterior():
    user, comedor, relevamiento = _escenario("prefill_solo_pendiente")
    _instancia(relevamiento, 1, PrimerSeguimiento.ESTADO_ASIGNADO, agua=True)

    response = _detalle(user, comedor)

    assert response.status_code == 200
    # La nº1 es la que se va a completar: no hay anterior de donde prellenar.
    assert response.data["seguimiento_anterior_mobile"] is None


@pytest.mark.django_db
def test_devuelve_la_instancia_inmediata_anterior_a_la_pendiente():
    user, comedor, relevamiento = _escenario("prefill_anterior")
    primer = _instancia(relevamiento, 1, PrimerSeguimiento.ESTADO_COMPLETO, agua=True)
    _instancia(
        relevamiento,
        2,
        PrimerSeguimiento.ESTADO_ASIGNADO,
        tipo=PrimerSeguimiento.TIPO_POSTERIOR,
    )

    response = _detalle(user, comedor)

    assert response.status_code == 200
    prefill = response.data["seguimiento_anterior_mobile"]
    assert prefill is not None
    assert prefill["id"] == primer.id
    assert prefill["numero_orden"] == 1
    assert prefill["estado"] == PrimerSeguimiento.ESTADO_COMPLETO


@pytest.mark.django_db
def test_el_prefill_trae_secciones_con_campo_y_valor():
    """Mismo formato que relevamiento_actual_mobile: campo + valor crudo."""
    user, comedor, relevamiento = _escenario("prefill_formato")
    _instancia(relevamiento, 1, PrimerSeguimiento.ESTADO_COMPLETO, agua=True)
    _instancia(
        relevamiento,
        2,
        PrimerSeguimiento.ESTADO_ASIGNADO,
        tipo=PrimerSeguimiento.TIPO_POSTERIOR,
    )

    response = _detalle(user, comedor)

    prefill = response.data["seguimiento_anterior_mobile"]
    seccion = next(s for s in prefill["sections"] if s["titulo"] == "Servicios básicos")
    agua = next(it for it in seccion["items"] if it["campo"] == "agua_potable")
    assert agua["valor"] is True
    assert "pregunta" in agua and "respuesta" in agua
    # `items` es el aplanado de todas las secciones.
    assert len(prefill["items"]) >= len(seccion["items"])


@pytest.mark.django_db
def test_con_todo_completo_devuelve_la_ultima_del_ciclo():
    user, comedor, relevamiento = _escenario("prefill_todo_completo")
    _instancia(relevamiento, 1, PrimerSeguimiento.ESTADO_COMPLETO, agua=False)
    ultima = _instancia(
        relevamiento,
        2,
        PrimerSeguimiento.ESTADO_COMPLETO,
        tipo=PrimerSeguimiento.TIPO_POSTERIOR,
        agua=True,
    )

    response = _detalle(user, comedor)

    prefill = response.data["seguimiento_anterior_mobile"]
    assert prefill["id"] == ultima.id
    assert prefill["numero_orden"] == 2


@pytest.mark.django_db
def test_solo_incluye_secciones_de_bloques_cargados():
    user, comedor, relevamiento = _escenario("prefill_bloques")
    _instancia(relevamiento, 1, PrimerSeguimiento.ESTADO_COMPLETO, agua=True)
    _instancia(
        relevamiento,
        2,
        PrimerSeguimiento.ESTADO_ASIGNADO,
        tipo=PrimerSeguimiento.TIPO_POSTERIOR,
    )

    response = _detalle(user, comedor)

    titulos = {
        s["titulo"] for s in response.data["seguimiento_anterior_mobile"]["sections"]
    }
    assert "Servicios básicos" in titulos
    # Los bloques que no se cargaron no generan seccion vacia.
    assert "Tarjeta" not in titulos
