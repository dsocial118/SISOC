"""Tests de la API server-to-server con la Ticketera.

Este módulo cubre el flag de habilitación y las regresiones específicas del
endurecimiento 2026-05-28 (carrera en el alta, idempotencia/409 case-insensitive,
idempotencia por origen Ticketera, fortaleza de contraseña y la IP en la
identidad del rate limit). Los happy-paths y la auditoría se cubren en
``tests/test_ticketera.py``.
"""

from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import IntegrityError
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_api_key.models import APIKey

# Contraseña que pasa AUTH_PASSWORD_VALIDATORS (>=8, no común, no numérica y no
# similar a los usernames usados en los tests).
STRONG_PASSWORD = "Ztr0ng!Passw0rd2026"


@pytest.fixture
def api_key(db):
    _, key = APIKey.objects.create_key(name="ticketera-tests")
    return key


@pytest.fixture
def api_client(api_key):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Api-Key {api_key}")
    return client


@pytest.fixture(autouse=True)
def _clear_rate_limit_cache():
    """Evita que el contador de rate limit se filtre entre tests."""
    cache.clear()
    yield
    cache.clear()


def _crear_usuario(username, *, source, password=STRONG_PASSWORD, email=None):
    user = User.objects.create_user(
        username=username,
        email=email or f"{username}@ejemplo.gob.ar",
        password=password,
    )
    profile = user.profile  # creado por el signal post_save de users
    profile.source = source
    profile.must_change_password = True
    profile.save(update_fields=["source", "must_change_password"])
    return user


# --------------------------------------------------------------------------- #
# Flag de habilitación
# --------------------------------------------------------------------------- #


@pytest.mark.smoke
@pytest.mark.django_db
@override_settings(TICKETERA_ENABLED=False)
def test_usuarios_responde_503_con_flag_deshabilitado(api_client):
    response = api_client.post(
        reverse("ticketera-usuarios"),
        {
            "username": "juan.perez",
            "email": "juan.perez@ejemplo.gob.ar",
            "password": "ContraseñaTemporal1!",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json()["error"] == "integration_disabled"


@pytest.mark.smoke
@pytest.mark.django_db
@override_settings(TICKETERA_ENABLED=False)
def test_verificar_responde_503_con_flag_deshabilitado(api_client):
    response = api_client.post(
        reverse("ticketera-auth-verificar"),
        {"username": "juan.perez", "password": "x"},
        format="json",
    )

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json()["error"] == "integration_disabled"


@pytest.mark.smoke
@pytest.mark.django_db
@override_settings(TICKETERA_ENABLED=False)
def test_cambiar_password_responde_503_con_flag_deshabilitado(api_client):
    response = api_client.post(
        reverse("ticketera-auth-cambiar-password"),
        {
            "username": "juan.perez",
            "current_password": "x",
            "new_password": "y",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json()["error"] == "integration_disabled"


@pytest.mark.smoke
@pytest.mark.django_db
@override_settings(TICKETERA_ENABLED=True)
def test_usuarios_opera_con_flag_habilitado(api_client):
    response = api_client.post(
        reverse("ticketera-usuarios"),
        {
            "username": "juan.perez",
            "email": "juan.perez@ejemplo.gob.ar",
            "password": "ContraseñaTemporal1!",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["username"] == "juan.perez"


# --------------------------------------------------------------------------- #
# Idempotencia / 409 case-insensitive (no normalizamos el username almacenado)
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
@override_settings(TICKETERA_ENABLED=True)
def test_usuarios_idempotente_case_insensitive_200(api_client):
    _crear_usuario("juan.perez", source="ticketera")

    response = api_client.post(
        reverse("ticketera-usuarios"),
        {
            "username": "Juan.Perez",
            "email": "otro@ejemplo.gob.ar",
            "password": STRONG_PASSWORD,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    # La diferencia de mayúsculas/minúsculas no debe crear un duplicado.
    assert User.objects.filter(username__iexact="juan.perez").count() == 1


@pytest.mark.django_db
@override_settings(TICKETERA_ENABLED=True)
def test_usuarios_conflicto_case_insensitive_409(api_client):
    _crear_usuario("ana.gomez", source="sisoc")

    response = api_client.post(
        reverse("ticketera-usuarios"),
        {
            "username": "ANA.GOMEZ",
            "email": "ana@ejemplo.gob.ar",
            "password": STRONG_PASSWORD,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["error"] == "username_taken"


@pytest.mark.django_db
@override_settings(TICKETERA_ENABLED=True)
def test_usuarios_idempotente_con_source_variante_ticketera_200(api_client):
    # Regresión: un alta previa con un source variante de Ticketera (p.ej.
    # "ticketera-qa") debe reconciliar idempotente (200), no chocar con 409.
    _crear_usuario("qa.user", source="ticketera-qa")

    response = api_client.post(
        reverse("ticketera-usuarios"),
        {
            "username": "qa.user",
            "email": "otro@ejemplo.gob.ar",
            "password": STRONG_PASSWORD,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert User.objects.filter(username__iexact="qa.user").count() == 1


# --------------------------------------------------------------------------- #
# Fortaleza de contraseña en el alta
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
@override_settings(TICKETERA_ENABLED=True)
def test_usuarios_password_debil_400_sin_crear(api_client):
    response = api_client.post(
        reverse("ticketera-usuarios"),
        {
            "username": "debil.user",
            "email": "debil@ejemplo.gob.ar",
            "password": "123",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "password" in response.json()
    assert not User.objects.filter(username__iexact="debil.user").exists()


# --------------------------------------------------------------------------- #
# Carrera en el alta: IntegrityError nunca devuelve 500
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
@override_settings(TICKETERA_ENABLED=True)
def test_usuarios_carrera_resuelve_200_si_ganador_es_ticketera(api_client):
    winner = _crear_usuario("race.user", source="ticketera")
    # Cachea el profile para no consultar la DB dentro del bloque mockeado.
    assert winner.profile.source == "ticketera"

    existing_qs = MagicMock()
    existing_qs.first.side_effect = [None, winner]  # pre-check, re-query
    with (
        patch.object(User.objects, "filter", return_value=existing_qs),
        patch.object(User.objects, "create_user", side_effect=IntegrityError("dup")),
    ):
        response = api_client.post(
            reverse("ticketera-usuarios"),
            {
                "username": "race.user",
                "email": "race@ejemplo.gob.ar",
                "password": STRONG_PASSWORD,
            },
            format="json",
        )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == "race.user"


@pytest.mark.django_db
@override_settings(TICKETERA_ENABLED=True)
def test_usuarios_carrera_resuelve_409_si_ganador_es_otro_source(api_client):
    winner = _crear_usuario("race.other", source="sisoc")
    assert winner.profile.source == "sisoc"

    existing_qs = MagicMock()
    existing_qs.first.side_effect = [None, winner]
    with (
        patch.object(User.objects, "filter", return_value=existing_qs),
        patch.object(User.objects, "create_user", side_effect=IntegrityError("dup")),
    ):
        response = api_client.post(
            reverse("ticketera-usuarios"),
            {
                "username": "race.other",
                "email": "race.other@ejemplo.gob.ar",
                "password": STRONG_PASSWORD,
            },
            format="json",
        )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["error"] == "username_taken"


# --------------------------------------------------------------------------- #
# Rate limit de verificar: la identidad incorpora la IP
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
@override_settings(TICKETERA_ENABLED=True)
def test_verificar_rate_limit_identity_incluye_ip(api_client):
    with patch("ticketera.api_views.hit_rate_limit", return_value=False) as rate_limit:
        api_client.post(
            reverse("ticketera-auth-verificar"),
            {"username": "juan.perez", "password": "x"},
            format="json",
            REMOTE_ADDR="203.0.113.5",
        )

    rate_limit.assert_called_once()
    assert rate_limit.call_args.kwargs["scope"] == "ticketera_verificar"
    assert rate_limit.call_args.kwargs["identity"] == "203.0.113.5:juan.perez"
