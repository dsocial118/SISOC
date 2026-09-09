"""Tests de las instancias de seguimiento (N14).

Un relevamiento pasa de tener UN primer seguimiento a tener N instancias del
ciclo (primer / posterior / virtual / acta de excepción), con ``numero_orden``,
endpoint propio por instancia y catálogo de motivos del acta.
"""

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from comedores.models import Comedor
from core.models import Provincia
from relevamientos.models import (
    ActaExcepcionSeguimiento,
    MotivoExcepcionSeguimiento,
    PrimerSeguimiento,
    Relevamiento,
)
from users.models import TerritorialComedorProvincia

SEGUIMIENTO_URL = "/api/relevamiento/seguimiento"
PRIMER_SEGUIMIENTO_URL = "/api/relevamiento/primer-seguimiento"
CATALOGO_URL = "/api/territorial/catalogos/motivos-excepcion-seguimiento/"

MOTIVOS_ESPERADOS = {
    "Espacio cerrado",
    "Dirección no encontrada",
    "Abierto sin entrevista",
    "Otro",
}


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


def _instancia(relevamiento, tipo, numero_orden, **kwargs):
    return PrimerSeguimiento.objects.create(
        id_relevamiento=relevamiento,
        tipo=tipo,
        numero_orden=numero_orden,
        estado=PrimerSeguimiento.ESTADO_ASIGNADO,
        **kwargs,
    )


# --------------------------------------------------------------------------- #
# Varias instancias por relevamiento
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_un_relevamiento_admite_varias_instancias_de_seguimiento():
    _, _, relevamiento = _escenario("n_instancias")

    primer = _instancia(relevamiento, PrimerSeguimiento.TIPO_PRIMER, 1)
    posterior = _instancia(relevamiento, PrimerSeguimiento.TIPO_POSTERIOR, 2)
    virtual = _instancia(relevamiento, PrimerSeguimiento.TIPO_VIRTUAL, 3)

    assert relevamiento.seguimientos.count() == 3
    assert {s.id for s in relevamiento.seguimientos.all()} == {
        primer.id,
        posterior.id,
        virtual.id,
    }


@pytest.mark.django_db
def test_no_admite_dos_instancias_con_el_mismo_numero_orden():
    _, _, relevamiento = _escenario("orden_unico")
    _instancia(relevamiento, PrimerSeguimiento.TIPO_PRIMER, 1)

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            _instancia(relevamiento, PrimerSeguimiento.TIPO_POSTERIOR, 1)


@pytest.mark.django_db
def test_property_primer_seguimiento_devuelve_la_instancia_uno():
    """Compatibilidad: el backoffice y los templates siguen usando este nombre."""
    _, _, relevamiento = _escenario("compat_property")
    primer = _instancia(relevamiento, PrimerSeguimiento.TIPO_PRIMER, 1)
    _instancia(relevamiento, PrimerSeguimiento.TIPO_POSTERIOR, 2)

    assert relevamiento.primer_seguimiento.id == primer.id


@pytest.mark.django_db
def test_property_primer_seguimiento_es_none_sin_instancias():
    _, _, relevamiento = _escenario("compat_vacio")

    assert relevamiento.primer_seguimiento is None


# --------------------------------------------------------------------------- #
# Exposición en el endpoint territorial
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_endpoint_territorial_lista_todas_las_instancias_ordenadas():
    user, comedor, relevamiento = _escenario("lista_instancias")
    _instancia(relevamiento, PrimerSeguimiento.TIPO_POSTERIOR, 2)
    _instancia(relevamiento, PrimerSeguimiento.TIPO_PRIMER, 1)
    _instancia(relevamiento, PrimerSeguimiento.TIPO_ACTA_EXCEPCION, 3)

    response = _token_client(user).get("/api/territorial/comedores/")

    assert response.status_code == 200
    row = next(r for r in response.data["results"] if r["id"] == comedor.id)
    items = row["seguimientos"]["items"]
    assert row["seguimientos"]["total"] == 3
    assert [it["numero_orden"] for it in items] == [1, 2, 3]
    assert [it["tipo"] for it in items] == ["primer", "posterior", "acta_excepcion"]
    assert all(it["id_relevamiento"] == relevamiento.id for it in items)


# --------------------------------------------------------------------------- #
# PATCH por instancia
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_patch_seguimiento_actualiza_la_instancia_indicada():
    user, _, relevamiento = _escenario("patch_instancia")
    primer = _instancia(relevamiento, PrimerSeguimiento.TIPO_PRIMER, 1)
    posterior = _instancia(relevamiento, PrimerSeguimiento.TIPO_POSTERIOR, 2)

    response = _token_client(user).patch(
        SEGUIMIENTO_URL,
        {"sisoc_id": posterior.id, "estado": PrimerSeguimiento.ESTADO_COMPLETO},
        format="json",
    )

    assert response.status_code == 200
    posterior.refresh_from_db()
    primer.refresh_from_db()
    assert posterior.estado == PrimerSeguimiento.ESTADO_COMPLETO
    # La instancia nº1 no se toca.
    assert primer.estado == PrimerSeguimiento.ESTADO_ASIGNADO


@pytest.mark.django_db
def test_primer_seguimiento_por_id_relevamiento_resuelve_la_instancia_uno():
    """Con N instancias, /primer-seguimiento sigue resolviendo la nº1."""
    user, _, relevamiento = _escenario("resolver_primer")
    primer = _instancia(relevamiento, PrimerSeguimiento.TIPO_PRIMER, 1)
    posterior = _instancia(relevamiento, PrimerSeguimiento.TIPO_POSTERIOR, 2)

    response = _token_client(user).patch(
        PRIMER_SEGUIMIENTO_URL,
        {
            "id_relevamiento": relevamiento.id,
            "estado": PrimerSeguimiento.ESTADO_COMPLETO,
        },
        format="json",
    )

    assert response.status_code == 200
    primer.refresh_from_db()
    posterior.refresh_from_db()
    assert primer.estado == PrimerSeguimiento.ESTADO_COMPLETO
    assert posterior.estado == PrimerSeguimiento.ESTADO_ASIGNADO


@pytest.mark.django_db
def test_seguimiento_por_id_relevamiento_con_varias_instancias_pide_sisoc_id():
    user, _, relevamiento = _escenario("resolver_ambiguo")
    _instancia(relevamiento, PrimerSeguimiento.TIPO_PRIMER, 1)
    _instancia(relevamiento, PrimerSeguimiento.TIPO_POSTERIOR, 2)

    response = _token_client(user).patch(
        SEGUIMIENTO_URL,
        {
            "id_relevamiento": relevamiento.id,
            "estado": PrimerSeguimiento.ESTADO_COMPLETO,
        },
        format="json",
    )

    assert response.status_code == 400
    assert "sisoc_id" in str(response.data)


# --------------------------------------------------------------------------- #
# Acta de excepción
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_acta_de_excepcion_se_persiste_con_motivo_por_nombre():
    user, _, relevamiento = _escenario("acta_ok")
    acta = _instancia(relevamiento, PrimerSeguimiento.TIPO_ACTA_EXCEPCION, 1)

    response = _token_client(user).patch(
        SEGUIMIENTO_URL,
        {
            "sisoc_id": acta.id,
            "estado": PrimerSeguimiento.ESTADO_COMPLETO,
            "acta_excepcion": {
                "motivo": "Espacio cerrado",
                "detalle": "Cerrado, vecinos informan mudanza",
                "firma": "https://example.com/firma.png",
            },
        },
        format="json",
    )

    assert response.status_code == 200
    acta.refresh_from_db()
    assert acta.acta_excepcion is not None
    assert acta.acta_excepcion.motivo.nombre == "Espacio cerrado"
    assert acta.acta_excepcion.detalle == "Cerrado, vecinos informan mudanza"
    assert acta.acta_excepcion.firma == "https://example.com/firma.png"


@pytest.mark.django_db
def test_acta_de_excepcion_con_motivo_invalido_devuelve_400():
    """El catálogo es cerrado: un motivo desconocido NO se crea, es 400."""
    user, _, relevamiento = _escenario("acta_invalida")
    acta = _instancia(relevamiento, PrimerSeguimiento.TIPO_ACTA_EXCEPCION, 1)

    response = _token_client(user).patch(
        SEGUIMIENTO_URL,
        {
            "sisoc_id": acta.id,
            "acta_excepcion": {"motivo": "Se me hizo tarde", "detalle": "x"},
        },
        format="json",
    )

    assert response.status_code == 400
    acta.refresh_from_db()
    assert acta.acta_excepcion is None
    assert not ActaExcepcionSeguimiento.objects.exists()
    # No se creó basura en el catálogo.
    assert not MotivoExcepcionSeguimiento.objects.filter(
        nombre="Se me hizo tarde"
    ).exists()


@pytest.mark.django_db
def test_acta_de_excepcion_reusa_la_fila_en_reintentos():
    user, _, relevamiento = _escenario("acta_dedup")
    acta = _instancia(relevamiento, PrimerSeguimiento.TIPO_ACTA_EXCEPCION, 1)
    payload = {
        "sisoc_id": acta.id,
        "acta_excepcion": {"motivo": "Otro", "detalle": "Primera versión"},
    }
    client = _token_client(user)

    assert client.patch(SEGUIMIENTO_URL, payload, format="json").status_code == 200
    payload["acta_excepcion"]["detalle"] = "Corregido"
    assert client.patch(SEGUIMIENTO_URL, payload, format="json").status_code == 200

    acta.refresh_from_db()
    assert ActaExcepcionSeguimiento.objects.count() == 1
    assert acta.acta_excepcion.detalle == "Corregido"


# --------------------------------------------------------------------------- #
# Catálogo de motivos
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_catalogo_de_motivos_del_acta_esta_sembrado():
    user, _, _ = _escenario("catalogo")

    response = _token_client(user).get(CATALOGO_URL)

    assert response.status_code == 200
    nombres = {item["nombre"] for item in response.data["items"]}
    assert MOTIVOS_ESPERADOS.issubset(nombres)
    assert all("id" in item for item in response.data["items"])


@pytest.mark.django_db
def test_catalogo_de_motivos_rechaza_no_territorial():
    user = get_user_model().objects.create_user(
        username="no_terr_catalogo",
        email="no_terr_catalogo@example.com",
        password="testpass123",
    )

    response = _token_client(user).get(CATALOGO_URL)

    assert response.status_code == 403
