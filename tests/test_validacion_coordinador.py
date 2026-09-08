"""Tests del ciclo de validación del coordinador (N16).

Cubre: el guard 409 sobre registros ``Validado``, la transición automática a
``Pendiente validación coordinador`` cuando el territorial reenvía, la exposición
de los campos en el endpoint territorial y la acción de revisión del backoffice.
"""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from rest_framework_api_key.models import APIKey

from comedores.models import Comedor
from core.models import Provincia
from relevamientos.models import PrimerSeguimiento, Relevamiento
from users.models import TerritorialComedorProvincia

PENDIENTE = Relevamiento.ESTADO_VALIDACION_PENDIENTE
A_SUBSANAR = Relevamiento.ESTADO_VALIDACION_A_SUBSANAR
VALIDADO = Relevamiento.ESTADO_VALIDACION_VALIDADO


def _token_client(user):
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


def _make_territorial(username, provincias):
    user = get_user_model().objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="testpass123",
    )
    user.profile.es_territorial_comedor = True
    user.profile.save(update_fields=["es_territorial_comedor"])
    for provincia in provincias:
        TerritorialComedorProvincia.objects.create(
            profile=user.profile, provincia=provincia
        )
    return user


def _comedor_con_relevamiento(nombre, user=None, **relevamiento_kwargs):
    provincia = Provincia.objects.create(nombre=f"Prov {nombre}")
    comedor = Comedor.objects.create(nombre=f"Comedor {nombre}", provincia=provincia)
    relevamiento = Relevamiento.objects.create(
        comedor=comedor,
        estado="Visita pendiente",
        territorial_user=user,
        **relevamiento_kwargs,
    )
    return provincia, comedor, relevamiento


# --------------------------------------------------------------------------- #
# Guard 409 sobre "Validado"
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_patch_relevamiento_validado_devuelve_409_sin_modificar():
    provincia, _, relevamiento = _comedor_con_relevamiento(
        "validado", estado_validacion=VALIDADO
    )
    user = _make_territorial("terr_validado", [provincia])
    relevamiento.territorial_user = user
    relevamiento.save(update_fields=["territorial_user"])

    response = _token_client(user).patch(
        "/api/relevamiento",
        {"sisoc_id": relevamiento.id, "estado": "Finalizado"},
        format="json",
    )

    assert response.status_code == 409
    assert response.data["estado_validacion"] == VALIDADO
    relevamiento.refresh_from_db()
    # No se tocó nada.
    assert relevamiento.estado == "Visita pendiente"
    assert relevamiento.estado_validacion == VALIDADO


@pytest.mark.django_db
def test_patch_seguimiento_validado_devuelve_409_sin_modificar():
    provincia, _, relevamiento = _comedor_con_relevamiento("seg_validado")
    user = _make_territorial("terr_seg_validado", [provincia])
    relevamiento.territorial_user = user
    relevamiento.save(update_fields=["territorial_user"])
    seguimiento = PrimerSeguimiento.objects.create(
        id_relevamiento=relevamiento,
        estado=PrimerSeguimiento.ESTADO_ASIGNADO,
        estado_validacion=VALIDADO,
    )

    response = _token_client(user).patch(
        "/api/relevamiento/primer-seguimiento",
        {"sisoc_id": seguimiento.id, "estado": PrimerSeguimiento.ESTADO_COMPLETO},
        format="json",
    )

    assert response.status_code == 409
    seguimiento.refresh_from_db()
    assert seguimiento.estado == PrimerSeguimiento.ESTADO_ASIGNADO
    assert seguimiento.estado_validacion == VALIDADO


@pytest.mark.django_db
def test_api_key_puede_patchear_un_relevamiento_validado():
    """El guard es solo para usuarios; la integración conserva escritura."""
    _, _, relevamiento = _comedor_con_relevamiento("apikey", estado_validacion=VALIDADO)
    _, key = APIKey.objects.create_key(name="gestionar-validacion")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Api-Key {key}")

    response = client.patch(
        "/api/relevamiento",
        {"sisoc_id": relevamiento.id, "estado": "Finalizado"},
        format="json",
    )

    assert response.status_code == 200
    relevamiento.refresh_from_db()
    assert relevamiento.estado == "Finalizado"


# --------------------------------------------------------------------------- #
# Transición automática al reenviar
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
@pytest.mark.parametrize("estado_previo", [None, A_SUBSANAR])
def test_patch_del_territorial_pasa_a_pendiente_validacion(estado_previo):
    provincia, _, relevamiento = _comedor_con_relevamiento(
        f"reenvio_{estado_previo or 'nulo'}", estado_validacion=estado_previo
    )
    user = _make_territorial(f"terr_reenvio_{estado_previo or 'nulo'}", [provincia])
    relevamiento.territorial_user = user
    relevamiento.save(update_fields=["territorial_user"])

    response = _token_client(user).patch(
        "/api/relevamiento",
        {"sisoc_id": relevamiento.id, "estado": "Finalizado"},
        format="json",
    )

    assert response.status_code == 200
    relevamiento.refresh_from_db()
    assert relevamiento.estado == "Finalizado"
    assert relevamiento.estado_validacion == PENDIENTE


@pytest.mark.django_db
def test_patch_sobre_pendiente_validacion_no_cambia_el_estado_de_validacion():
    provincia, _, relevamiento = _comedor_con_relevamiento(
        "ya_pendiente", estado_validacion=PENDIENTE
    )
    user = _make_territorial("terr_ya_pendiente", [provincia])
    relevamiento.territorial_user = user
    relevamiento.save(update_fields=["territorial_user"])

    response = _token_client(user).patch(
        "/api/relevamiento",
        {"sisoc_id": relevamiento.id, "estado": "Finalizado"},
        format="json",
    )

    assert response.status_code == 200
    relevamiento.refresh_from_db()
    assert relevamiento.estado_validacion == PENDIENTE


@pytest.mark.django_db
def test_patch_seguimiento_a_subsanar_pasa_a_pendiente_validacion():
    provincia, _, relevamiento = _comedor_con_relevamiento("seg_reenvio")
    user = _make_territorial("terr_seg_reenvio", [provincia])
    relevamiento.territorial_user = user
    relevamiento.save(update_fields=["territorial_user"])
    seguimiento = PrimerSeguimiento.objects.create(
        id_relevamiento=relevamiento,
        estado=PrimerSeguimiento.ESTADO_ASIGNADO,
        estado_validacion=A_SUBSANAR,
    )

    response = _token_client(user).patch(
        "/api/relevamiento/primer-seguimiento",
        {"sisoc_id": seguimiento.id, "estado": PrimerSeguimiento.ESTADO_COMPLETO},
        format="json",
    )

    assert response.status_code == 200
    seguimiento.refresh_from_db()
    assert seguimiento.estado == PrimerSeguimiento.ESTADO_COMPLETO
    assert seguimiento.estado_validacion == PENDIENTE


# --------------------------------------------------------------------------- #
# Exposición en el endpoint territorial
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_endpoint_territorial_expone_campos_de_validacion():
    provincia = Provincia.objects.create(nombre="Prov Validacion API")
    comedor = Comedor.objects.create(nombre="Comedor Val API", provincia=provincia)
    user = _make_territorial("terr_val_api", [provincia])
    relevamiento = Relevamiento.objects.create(
        comedor=comedor,
        estado="Finalizado",
        territorial_user=user,
        estado_validacion=A_SUBSANAR,
        observaciones_coordinador="Faltan fotos de la cocina.",
    )
    PrimerSeguimiento.objects.create(
        id_relevamiento=relevamiento,
        estado=PrimerSeguimiento.ESTADO_COMPLETO,
        estado_validacion=VALIDADO,
    )

    response = _token_client(user).get("/api/territorial/comedores/")

    assert response.status_code == 200
    row = next(r for r in response.data["results"] if r["id"] == comedor.id)
    item = next(
        it for it in row["relevamientos"]["items"] if it["id"] == relevamiento.id
    )
    assert item["estado_validacion"] == A_SUBSANAR
    assert item["observaciones_coordinador"] == "Faltan fotos de la cocina."
    assert "fecha_revision_coordinador" in item

    seguimiento_item = row["seguimientos"]["items"][0]
    assert seguimiento_item["estado_validacion"] == VALIDADO
    assert seguimiento_item["observaciones_coordinador"] is None


# --------------------------------------------------------------------------- #
# Acción de revisión del backoffice
# --------------------------------------------------------------------------- #


def _coordinador(client, username="coordinador"):
    user = get_user_model().objects.create_user(
        username=username, password="testpass123"
    )
    user.user_permissions.add(
        Permission.objects.get(
            content_type__app_label="relevamientos",
            codename="review_relevamiento",
        )
    )
    client.force_login(user)
    return user


@pytest.mark.django_db
def test_coordinador_valida_el_relevamiento(client):
    _, comedor, relevamiento = _comedor_con_relevamiento("revision_ok")
    coordinador = _coordinador(client, "coord_valida")
    url = reverse(
        "relevamiento_revision_coordinador",
        kwargs={"comedor_pk": comedor.id, "pk": relevamiento.id},
    )

    response = client.post(url, {"estado_validacion": VALIDADO})

    assert response.status_code == 302
    relevamiento.refresh_from_db()
    assert relevamiento.estado_validacion == VALIDADO
    assert relevamiento.coordinador_id == coordinador.id
    assert relevamiento.fecha_revision_coordinador is not None


@pytest.mark.django_db
def test_coordinador_devuelve_a_subsanar_con_observaciones(client):
    _, comedor, relevamiento = _comedor_con_relevamiento("revision_devuelve")
    _coordinador(client, "coord_devuelve")
    url = reverse(
        "relevamiento_revision_coordinador",
        kwargs={"comedor_pk": comedor.id, "pk": relevamiento.id},
    )

    response = client.post(
        url,
        {
            "estado_validacion": A_SUBSANAR,
            "observaciones_coordinador": "Falta la firma del referente.",
        },
    )

    assert response.status_code == 302
    relevamiento.refresh_from_db()
    assert relevamiento.estado_validacion == A_SUBSANAR
    assert relevamiento.observaciones_coordinador == "Falta la firma del referente."


@pytest.mark.django_db
def test_devolver_sin_observaciones_no_cambia_nada(client):
    _, comedor, relevamiento = _comedor_con_relevamiento("revision_sin_obs")
    _coordinador(client, "coord_sin_obs")
    url = reverse(
        "relevamiento_revision_coordinador",
        kwargs={"comedor_pk": comedor.id, "pk": relevamiento.id},
    )

    response = client.post(url, {"estado_validacion": A_SUBSANAR})

    assert response.status_code == 302
    relevamiento.refresh_from_db()
    assert relevamiento.estado_validacion is None
    assert relevamiento.observaciones_coordinador is None


@pytest.mark.django_db
def test_usuario_sin_permiso_no_puede_revisar(client):
    _, comedor, relevamiento = _comedor_con_relevamiento("revision_sin_perm")
    user = get_user_model().objects.create_user(
        username="sin_permiso_revision", password="testpass123"
    )
    client.force_login(user)
    url = reverse(
        "relevamiento_revision_coordinador",
        kwargs={"comedor_pk": comedor.id, "pk": relevamiento.id},
    )

    response = client.post(url, {"estado_validacion": VALIDADO})

    assert response.status_code in {302, 403}
    relevamiento.refresh_from_db()
    assert relevamiento.estado_validacion is None
