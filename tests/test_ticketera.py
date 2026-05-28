"""Tests de la API server-to-server con la Ticketera.

Cubre los tres endpoints protegidos por API Key:
- POST /api/ticketera/usuarios/              (alta / reconciliación)
- POST /api/ticketera/auth/verificar/        (verificación de credenciales)
- POST /api/ticketera/auth/cambiar-password/ (cambio de contraseña temporal)

Reutiliza las fixtures `api_key` / `api_client` de ``tests/conftest.py`` (cliente
DRF con header ``Authorization: Api-Key <key>``).
"""

import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APIClient

from auditlog.models import LogEntry
from audittrail.models import AuditEntryMeta


USUARIOS_URL = "/api/ticketera/usuarios/"
VERIFICAR_URL = "/api/ticketera/auth/verificar/"
CAMBIAR_PASSWORD_URL = "/api/ticketera/auth/cambiar-password/"
AUDIT_SOURCE = "ticketera"


@pytest.fixture(autouse=True)
def _clear_rate_limit_cache():
    """LocMemCache persiste entre tests; lo limpiamos para no arrastrar el rate limit."""
    cache.clear()
    yield
    cache.clear()


def _crear_usuario(
    *,
    username,
    password="ClaveSegura123!",
    source="sisoc",
    must_change_password=False,
    is_active=True,
):
    """Crea un User con su Profile (el Profile lo crea el signal post_save de users)."""
    user = User.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password=password,
        is_active=is_active,
    )
    profile = user.profile
    profile.source = source
    profile.must_change_password = must_change_password
    profile.save(update_fields=["source", "must_change_password"])
    return user


# --------------------------------------------------------------------------- #
# POST /usuarios/  (alta / reconciliación)
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_usuarios_alta_nueva_devuelve_201_y_setea_profile(api_client):
    payload = {
        "username": "juan.perez",
        "email": "juan.perez@ejemplo.gob.ar",
        "first_name": "Juan",
        "last_name": "Pérez",
        "password": "ContraseñaTemporal1!",
    }

    response = api_client.post(USUARIOS_URL, payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    user = User.objects.get(username="juan.perez")
    assert response.data == {
        "id": user.id,
        "username": "juan.perez",
        "email": "juan.perez@ejemplo.gob.ar",
    }
    assert user.first_name == "Juan"
    assert user.check_password("ContraseñaTemporal1!") is True
    # default cuando el body no manda source
    assert user.profile.source == "ticketera"
    assert user.profile.must_change_password is True


@pytest.mark.django_db
def test_usuarios_alta_respeta_source_del_body(api_client):
    payload = {
        "username": "ana.gomez",
        "email": "ana.gomez@ejemplo.gob.ar",
        "password": "ContraseñaTemporal1!",
        "source": "ticketera-qa",
    }

    response = api_client.post(USUARIOS_URL, payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert User.objects.get(username="ana.gomez").profile.source == "ticketera-qa"


@pytest.mark.django_db
def test_usuarios_idempotente_devuelve_200_sin_duplicar(api_client):
    existente = _crear_usuario(username="repetido", source="ticketera")
    total_antes = User.objects.count()

    payload = {
        "username": "repetido",
        "email": "otro-mail@ejemplo.gob.ar",
        "password": "OtraClave1!",
    }
    response = api_client.post(USUARIOS_URL, payload, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert response.data == {
        "id": existente.id,
        "username": "repetido",
        "email": "repetido@example.com",  # se devuelve el mail existente, no el del payload
    }
    assert User.objects.count() == total_antes  # no se creó un duplicado


@pytest.mark.django_db
def test_usuarios_username_tomado_por_otro_source_devuelve_409(api_client):
    _crear_usuario(username="ocupado", source="sisoc")
    total_antes = User.objects.count()

    payload = {
        "username": "ocupado",
        "email": "nuevo@ejemplo.gob.ar",
        "password": "Clave1!",
    }
    response = api_client.post(USUARIOS_URL, payload, format="json")

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.data["error"] == "username_taken"
    assert User.objects.count() == total_antes


@pytest.mark.django_db
@pytest.mark.parametrize(
    "payload",
    [
        pytest.param(
            {"username": "sin.email", "password": "Clave1!"},
            id="email-faltante",
        ),
        pytest.param(
            {
                "username": "mail.malo",
                "email": "no-es-un-email",
                "password": "Clave1!",
            },
            id="email-invalido",
        ),
        pytest.param(
            {"username": "sin.pass", "email": "sin.pass@ejemplo.gob.ar"},
            id="password-faltante",
        ),
    ],
)
def test_usuarios_payload_invalido_devuelve_400(api_client, payload):
    response = api_client.post(USUARIOS_URL, payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not User.objects.filter(username=payload["username"]).exists()


# --------------------------------------------------------------------------- #
# POST /auth/verificar/
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_verificar_credenciales_validas_devuelve_200(api_client):
    user = _crear_usuario(
        username="valido",
        password="ClaveOk123!",
        source="ticketera",
        must_change_password=True,
    )

    response = api_client.post(
        VERIFICAR_URL,
        {"username": "valido", "password": "ClaveOk123!"},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["valid"] is True
    # must_change_password se refleja desde el Profile
    assert response.data["must_change_password"] is True
    assert response.data["user"] == {
        "id": user.id,
        "username": "valido",
        "email": "valido@example.com",
        "first_name": "",
        "last_name": "",
    }


@pytest.mark.django_db
def test_verificar_password_incorrecta_devuelve_401(api_client):
    user = _crear_usuario(username="claveok", password="LaBuena123!")

    response = api_client.post(
        VERIFICAR_URL,
        {"username": "claveok", "password": "LaMala123!"},
        format="json",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data == {"valid": False, "error": "invalid_credentials"}
    # Una verificación fallida no debe registrar un acceso.
    assert (
        LogEntry.objects.get_for_object(user)
        .filter(action=LogEntry.Action.ACCESS)
        .count()
        == 0
    )


@pytest.mark.django_db
def test_verificar_usuario_inactivo_devuelve_401(api_client):
    _crear_usuario(username="inactivo", password="ClaveOk123!", is_active=False)

    response = api_client.post(
        VERIFICAR_URL,
        {"username": "inactivo", "password": "ClaveOk123!"},
        format="json",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data == {"valid": False, "error": "invalid_credentials"}


@pytest.mark.django_db
def test_verificar_supera_rate_limit_devuelve_429_en_el_intento_11(api_client):
    user = _crear_usuario(username="bruteforce", password="ClaveOk123!")

    # Límite: 10 intentos por username (window 300s). Los primeros 10 pasan el
    # rate limit y fallan por credenciales; el 11° ya queda bloqueado.
    for _ in range(10):
        previo = api_client.post(
            VERIFICAR_URL,
            {"username": "bruteforce", "password": "incorrecta"},
            format="json",
        )
        assert previo.status_code == status.HTTP_401_UNAUTHORIZED

    bloqueado = api_client.post(
        VERIFICAR_URL,
        {"username": "bruteforce", "password": "incorrecta"},
        format="json",
    )

    assert bloqueado.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert bloqueado.data["error"] == "too_many_attempts"
    # Ni los intentos fallidos ni el bloqueo registran un acceso.
    assert (
        LogEntry.objects.get_for_object(user)
        .filter(action=LogEntry.Action.ACCESS)
        .count()
        == 0
    )


# --------------------------------------------------------------------------- #
# POST /auth/cambiar-password/
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_cambiar_password_cierra_ciclo_temporal(api_client):
    _crear_usuario(
        username="cambia.pass",
        password="TemporalInicial1!",
        source="ticketera",
        must_change_password=True,
    )

    response = api_client.post(
        CAMBIAR_PASSWORD_URL,
        {
            "username": "cambia.pass",
            "current_password": "TemporalInicial1!",
            "new_password": "DefinitivaSegura9!",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data == {"changed": True, "must_change_password": False}

    user = User.objects.get(username="cambia.pass")
    assert user.check_password("DefinitivaSegura9!") is True
    assert user.profile.must_change_password is False

    # Criterio de aceptación: un verificar posterior refleja el flag bajado.
    verificacion = api_client.post(
        VERIFICAR_URL,
        {"username": "cambia.pass", "password": "DefinitivaSegura9!"},
        format="json",
    )
    assert verificacion.status_code == status.HTTP_200_OK
    assert verificacion.data["must_change_password"] is False


@pytest.mark.django_db
def test_cambiar_password_current_incorrecta_devuelve_401_sin_cambios(api_client):
    _crear_usuario(
        username="mala.actual",
        password="TemporalInicial1!",
        source="ticketera",
        must_change_password=True,
    )

    response = api_client.post(
        CAMBIAR_PASSWORD_URL,
        {
            "username": "mala.actual",
            "current_password": "NoEsLaActual1!",
            "new_password": "DefinitivaSegura9!",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data == {"error": "invalid_credentials"}

    user = User.objects.get(username="mala.actual")
    # La temporal sigue vigente y el flag no se baja.
    assert user.check_password("TemporalInicial1!") is True
    assert user.profile.must_change_password is True


@pytest.mark.django_db
def test_cambiar_password_usuario_inactivo_devuelve_401(api_client):
    _crear_usuario(
        username="inactivo.pass",
        password="TemporalInicial1!",
        source="ticketera",
        must_change_password=True,
        is_active=False,
    )

    response = api_client.post(
        CAMBIAR_PASSWORD_URL,
        {
            "username": "inactivo.pass",
            "current_password": "TemporalInicial1!",
            "new_password": "DefinitivaSegura9!",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data == {"error": "invalid_credentials"}


@pytest.mark.django_db
def test_cambiar_password_nueva_debil_devuelve_400_sin_cambios(api_client):
    _crear_usuario(
        username="debil.nueva",
        password="TemporalInicial1!",
        source="ticketera",
        must_change_password=True,
    )

    response = api_client.post(
        CAMBIAR_PASSWORD_URL,
        {
            "username": "debil.nueva",
            "current_password": "TemporalInicial1!",
            "new_password": "123",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "new_password" in response.data

    user = User.objects.get(username="debil.nueva")
    assert user.check_password("TemporalInicial1!") is True
    assert user.profile.must_change_password is True


@pytest.mark.django_db
def test_cambiar_password_igual_a_la_actual_devuelve_400_sin_cambios(api_client):
    _crear_usuario(
        username="igual.actual",
        password="TemporalInicial1!",
        source="ticketera",
        must_change_password=True,
    )

    response = api_client.post(
        CAMBIAR_PASSWORD_URL,
        {
            "username": "igual.actual",
            "current_password": "TemporalInicial1!",
            "new_password": "TemporalInicial1!",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "new_password" in response.data

    user = User.objects.get(username="igual.actual")
    assert user.profile.must_change_password is True


@pytest.mark.django_db
def test_cambiar_password_supera_rate_limit_devuelve_429_en_el_intento_11(api_client):
    _crear_usuario(
        username="bruteforce.pass",
        password="TemporalInicial1!",
        source="ticketera",
        must_change_password=True,
    )

    # Límite: 10 intentos por ip:username (window 300s). Los primeros 10 pasan
    # el rate limit y fallan por credenciales; el 11° ya queda bloqueado.
    for _ in range(10):
        previo = api_client.post(
            CAMBIAR_PASSWORD_URL,
            {
                "username": "bruteforce.pass",
                "current_password": "incorrecta",
                "new_password": "DefinitivaSegura9!",
            },
            format="json",
        )
        assert previo.status_code == status.HTTP_401_UNAUTHORIZED

    bloqueado = api_client.post(
        CAMBIAR_PASSWORD_URL,
        {
            "username": "bruteforce.pass",
            "current_password": "incorrecta",
            "new_password": "DefinitivaSegura9!",
        },
        format="json",
    )

    assert bloqueado.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert bloqueado.data["error"] == "too_many_attempts"


@pytest.mark.django_db
def test_cambiar_password_registra_auditoria_con_source_ticketera(api_client):
    user = _crear_usuario(
        username="audita.cambio",
        password="TemporalInicial1!",
        source="ticketera",
        must_change_password=True,
    )
    updates_antes = (
        LogEntry.objects.get_for_object(user)
        .filter(action=LogEntry.Action.UPDATE)
        .count()
    )

    response = api_client.post(
        CAMBIAR_PASSWORD_URL,
        {
            "username": "audita.cambio",
            "current_password": "TemporalInicial1!",
            "new_password": "DefinitivaSegura9!",
        },
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK

    updates = LogEntry.objects.get_for_object(user).filter(
        action=LogEntry.Action.UPDATE
    )
    assert updates.count() == updates_antes + 1

    entry = updates.latest("id")
    assert entry.actor_id == user.id
    meta = entry.audittrail_meta
    assert meta.source == AUDIT_SOURCE
    remote_source = (meta.extra.get("context") or {}).get("remote_source") or (
        meta.extra.get("custom_signal_context") or {}
    ).get("remote_source")
    assert remote_source == "ticketera"


# --------------------------------------------------------------------------- #
# Permisos (API Key)
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
@pytest.mark.parametrize("url", [USUARIOS_URL, VERIFICAR_URL, CAMBIAR_PASSWORD_URL])
def test_sin_api_key_rechaza(url):
    client = APIClient()  # sin header Authorization: Api-Key

    response = client.post(
        url,
        {"username": "x", "password": "y", "email": "x@ejemplo.gob.ar"},
        format="json",
    )

    # HasAPIKey deniega; con los autenticadores DRF por defecto (Token/Session)
    # el status real esperado es 401, pero aceptamos 403 por robustez.
    assert response.status_code in (
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    )


# --------------------------------------------------------------------------- #
# Auditoría (django-auditlog + AuditEntryMeta)
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_alta_registra_auditoria_con_source_ticketera(api_client):
    metas_antes = AuditEntryMeta.objects.filter(source=AUDIT_SOURCE).count()

    payload = {
        "username": "auditado",
        "email": "auditado@ejemplo.gob.ar",
        "password": "ContraseñaTemporal1!",
    }
    response = api_client.post(USUARIOS_URL, payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED

    metas = AuditEntryMeta.objects.filter(source=AUDIT_SOURCE)
    assert metas.count() == metas_antes + 1

    user = User.objects.get(username="auditado")
    meta = metas.latest("id")
    assert meta.log_entry.action == LogEntry.Action.CREATE
    assert meta.log_entry.object_pk == str(user.pk)
    assert meta.extra.get("context") == {"remote_source": "ticketera"}


@pytest.mark.django_db
def test_verificar_valido_registra_acceso(api_client):
    # `last_login` está excluido del diff de auditoría (audittrail.constants): el
    # save no deja rastro, así que la vista emite un LogEntry ACCESS explícito para
    # que el acceso quede en el historial con su source y remote_source.
    user = _crear_usuario(username="conlog", password="ClaveOk123!", source="ticketera")
    accesos_antes = (
        LogEntry.objects.get_for_object(user)
        .filter(action=LogEntry.Action.ACCESS)
        .count()
    )

    response = api_client.post(
        VERIFICAR_URL,
        {"username": "conlog", "password": "ClaveOk123!"},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK

    accesos = LogEntry.objects.get_for_object(user).filter(
        action=LogEntry.Action.ACCESS
    )
    assert accesos.count() == accesos_antes + 1

    entry = accesos.latest("id")
    assert entry.actor_id == user.id
    meta = entry.audittrail_meta
    assert meta.source == AUDIT_SOURCE
    remote_source = (meta.extra.get("context") or {}).get("remote_source") or (
        meta.extra.get("custom_signal_context") or {}
    ).get("remote_source")
    assert remote_source == "ticketera"
