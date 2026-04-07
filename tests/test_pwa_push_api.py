import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from comedores.models import Comedor
from core.models import Provincia
from organizaciones.models import Organizacion
from pwa.models import PushSubscriptionPWA
from rendicioncuentasmensual.models import DocumentacionAdjunta, RendicionCuentaMensual
from rendicioncuentasmensual.services import RendicionCuentaMensualService
from users.models import AccesoComedorPWA


def _create_pwa_user(*, comedor, username, role=AccesoComedorPWA.ROL_REPRESENTANTE):
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="testpass123",
    )
    AccesoComedorPWA.objects.create(
        user=user,
        comedor=comedor,
        rol=role,
        activo=True,
    )
    return user


def _auth_client_for_user(user):
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


def _grant_mobile_rendicion_permission(user):
    permission = Permission.objects.get(
        content_type__app_label="rendicioncuentasmensual",
        codename="manage_mobile_rendicion",
    )
    user.user_permissions.add(permission)


@pytest.fixture
def espacios_push(db):
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    organizacion = Organizacion.objects.create(nombre="Organizacion Push")
    espacio_1 = Comedor.objects.create(
        nombre="Espacio Push Uno",
        provincia=provincia,
        organizacion=organizacion,
        codigo_de_proyecto="PROY-PUSH",
    )
    espacio_2 = Comedor.objects.create(
        nombre="Espacio Push Dos",
        provincia=provincia,
        organizacion=organizacion,
        codigo_de_proyecto="PROY-PUSH",
    )
    espacio_3 = Comedor.objects.create(
        nombre="Espacio Push Tres",
        provincia=provincia,
        organizacion=organizacion,
        codigo_de_proyecto="PROY-OTRO",
    )
    return espacio_1, espacio_2, espacio_3


@pytest.mark.django_db
def test_push_subscription_endpoints_create_and_delete(
    monkeypatch,
    espacios_push,
    settings,
):
    settings.PWA_WEB_PUSH_PUBLIC_KEY = "public-test-key"
    settings.PWA_WEB_PUSH_PRIVATE_KEY = "private-test-key"
    settings.PWA_WEB_PUSH_SUBJECT = "mailto:test@example.com"
    settings.PWA_WEB_PUSH_ENABLED = True

    espacio_1, _, _ = espacios_push
    user = _create_pwa_user(comedor=espacio_1, username="push_api_user")
    authed_client = _auth_client_for_user(user)
    monkeypatch.setattr("pwa.api_views.web_push_enabled", lambda: False)

    config_response = authed_client.get("/api/pwa/push/config/")

    assert config_response.status_code == 200
    assert config_response.data == {
        "enabled": False,
        "public_key": "public-test-key",
    }

    create_response = authed_client.post(
        "/api/pwa/push/subscriptions/",
        {
            "endpoint": "https://push.example.com/subscription/1",
            "p256dh": "p256dh-key",
            "auth": "auth-key",
            "content_encoding": "aes128gcm",
        },
        format="json",
    )

    assert create_response.status_code == 201
    subscription = PushSubscriptionPWA.objects.get(
        endpoint="https://push.example.com/subscription/1"
    )
    assert subscription.user == user
    assert subscription.activo is True

    delete_response = authed_client.delete(
        "/api/pwa/push/subscriptions/",
        {"endpoint": "https://push.example.com/subscription/1"},
        format="json",
    )

    assert delete_response.status_code == 204
    subscription.refresh_from_db()
    assert subscription.activo is False


@pytest.mark.django_db
def test_revision_de_rendicion_envia_push_a_usuarios_del_scope_con_permiso(
    monkeypatch,
    espacios_push,
    settings,
):
    settings.PWA_WEB_PUSH_PUBLIC_KEY = "public-test-key"
    settings.PWA_WEB_PUSH_PRIVATE_KEY = "private-test-key"
    settings.PWA_WEB_PUSH_SUBJECT = "mailto:test@example.com"
    settings.PWA_WEB_PUSH_ENABLED = True

    espacio_1, espacio_2, espacio_3 = espacios_push
    actor = _create_pwa_user(comedor=espacio_1, username="push_actor")
    _grant_mobile_rendicion_permission(actor)

    receptor_ok = _create_pwa_user(comedor=espacio_2, username="push_scope_ok")
    _grant_mobile_rendicion_permission(receptor_ok)
    receptor_sin_permiso = _create_pwa_user(
        comedor=espacio_1,
        username="push_scope_sin_permiso",
    )
    receptor_fuera_scope = _create_pwa_user(
        comedor=espacio_3,
        username="push_scope_fuera",
    )
    _grant_mobile_rendicion_permission(receptor_fuera_scope)

    PushSubscriptionPWA.objects.create(
        user=receptor_ok,
        endpoint="https://push.example.com/ok",
        p256dh="k1",
        auth="a1",
    )
    PushSubscriptionPWA.objects.create(
        user=receptor_sin_permiso,
        endpoint="https://push.example.com/no-perm",
        p256dh="k2",
        auth="a2",
    )
    PushSubscriptionPWA.objects.create(
        user=receptor_fuera_scope,
        endpoint="https://push.example.com/out",
        p256dh="k3",
        auth="a3",
    )

    sent = []

    monkeypatch.setattr(
        "pwa.services.push_service.web_push_enabled",
        lambda: True,
    )

    def fake_send_push(subscription, payload):
        sent.append(
            {
                "user_id": subscription.user_id,
                "endpoint": subscription.endpoint,
                "payload": payload,
            }
        )
        return True

    monkeypatch.setattr("pwa.services.push_service._send_push", fake_send_push)

    rendicion = RendicionCuentaMensual.objects.create(
        comedor=espacio_1,
        mes=4,
        anio=2026,
        convenio="Convenio Push",
        numero_rendicion=77,
        periodo_inicio=timezone.now().date(),
        periodo_fin=timezone.now().date(),
        estado=RendicionCuentaMensual.ESTADO_REVISION,
    )
    documento = DocumentacionAdjunta.objects.create(
        nombre="comprobante.pdf",
        categoria=DocumentacionAdjunta.CATEGORIA_COMPROBANTES,
        estado=DocumentacionAdjunta.ESTADO_PRESENTADO,
        rendicion_cuenta_mensual=rendicion,
        archivo=SimpleUploadedFile(
            "comprobante.pdf",
            b"pdf",
            content_type="application/pdf",
        ),
    )

    RendicionCuentaMensualService.actualizar_estado_documento_revision(
        documento=documento,
        estado=DocumentacionAdjunta.ESTADO_SUBSANAR,
        observaciones="Falta detalle",
        actor=actor,
    )

    assert len(sent) == 1
    user_ids = {item["user_id"] for item in sent}
    assert user_ids == {receptor_ok.id}
    payload = sent[0]["payload"]
    assert payload["data"]["tipo"] == "rendicion_detalle"
    assert payload["data"]["rendicion_id"] == rendicion.id
    assert payload["data"]["space_id"] == espacio_1.id
    assert payload["data"]["url"] == (
        f"/app-org/espacios/{espacio_1.id}/rendicion/{rendicion.id}"
    )
