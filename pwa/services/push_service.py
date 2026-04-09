import json
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from iam.services import user_has_permission_code
from pwa.models import (
    PushSubscriptionPWA,
    build_push_endpoint_hash,
    normalize_push_endpoint,
)
from users.services_pwa import get_accessible_comedor_ids
from users.models import AccesoComedorPWA

try:
    from pywebpush import WebPushException, webpush
except ImportError:  # pragma: no cover - depende de entorno
    WebPushException = Exception
    webpush = None

LOGGER = logging.getLogger("django")
User = get_user_model()


def web_push_enabled() -> bool:
    return bool(settings.PWA_WEB_PUSH_ENABLED and webpush)


def upsert_push_subscription(
    *,
    user,
    endpoint: str,
    p256dh: str,
    auth: str,
    content_encoding: str = "aes128gcm",
    user_agent: str | None = None,
):
    now = timezone.now()
    normalized_endpoint = normalize_push_endpoint(endpoint)
    endpoint_hash = build_push_endpoint_hash(normalized_endpoint)
    subscription, created = PushSubscriptionPWA.objects.update_or_create(
        endpoint_hash=endpoint_hash,
        defaults={
            "endpoint": normalized_endpoint,
            "user": user,
            "p256dh": p256dh,
            "auth": auth,
            "content_encoding": content_encoding or "aes128gcm",
            "user_agent": (user_agent or "")[:512] or None,
            "activo": True,
            "fecha_baja": None,
            "fecha_actualizacion": now,
        },
    )
    return subscription, created


def deactivate_push_subscription(*, user, endpoint: str) -> bool:
    endpoint_hash = build_push_endpoint_hash(endpoint)
    updated = PushSubscriptionPWA.objects.filter(
        user=user,
        endpoint_hash=endpoint_hash,
        activo=True,
    ).update(
        activo=False,
        fecha_baja=timezone.now(),
        fecha_actualizacion=timezone.now(),
    )
    return bool(updated)


def build_rendicion_push_payload(
    *,
    comunicado,
    rendicion,
    target_comedor_id: int | None = None,
) -> dict:
    comedor_id = target_comedor_id or rendicion.comedor_id
    return {
        "title": comunicado.titulo,
        "body": comunicado.cuerpo.replace(
            "[SISOC_ACCION]rendicion_detalle:" f"{rendicion.id}[/SISOC_ACCION]",
            "",
        ).strip(),
        "icon": "/icono.png",
        "badge": "/icono.png",
        "tag": f"rendicion-{rendicion.id}",
        "data": {
            "tipo": "rendicion_detalle",
            "rendicion_id": rendicion.id,
            "space_id": comedor_id,
            "comunicado_id": comunicado.id,
            "url": f"/app-org/espacios/{comedor_id}/rendicion/{rendicion.id}",
        },
    }


def _resolve_target_comedor_id_for_user(
    *,
    user,
    comedor_ids: list[int],
    rendicion,
) -> int | None:
    accessible_comedor_ids = set(get_accessible_comedor_ids(user))
    scoped_comedor_ids = [
        comedor_id for comedor_id in comedor_ids if comedor_id in accessible_comedor_ids
    ]
    if not scoped_comedor_ids:
        return None
    if rendicion.comedor_id in scoped_comedor_ids:
        return rendicion.comedor_id
    return scoped_comedor_ids[0]


def _deactivate_subscription_for_delivery_failure(subscription) -> None:
    subscription.activo = False
    subscription.fecha_baja = timezone.now()
    subscription.save(update_fields=["activo", "fecha_baja", "fecha_actualizacion"])


def _send_push(subscription, payload: dict) -> bool:
    if not web_push_enabled():
        return False

    try:
        webpush(
            subscription_info={
                "endpoint": subscription.endpoint,
                "keys": {
                    "p256dh": subscription.p256dh,
                    "auth": subscription.auth,
                },
            },
            data=json.dumps(payload),
            vapid_private_key=settings.PWA_WEB_PUSH_PRIVATE_KEY,
            vapid_claims={"sub": settings.PWA_WEB_PUSH_SUBJECT},
        )
        return True
    except WebPushException as exc:  # pragma: no cover - depende de proveedor push
        response = getattr(exc, "response", None)
        if getattr(response, "status_code", None) in (404, 410):
            _deactivate_subscription_for_delivery_failure(subscription)
        LOGGER.warning(
            "No se pudo enviar web push PWA",
            extra={
                "user_id": subscription.user_id,
                "endpoint": subscription.endpoint,
                "status_code": getattr(response, "status_code", None),
            },
        )
    except Exception:  # pragma: no cover - defensivo
        LOGGER.exception(
            "Error inesperado enviando web push PWA",
            extra={"user_id": subscription.user_id},
        )
    return False


def _get_users_with_permission_for_project_scope(
    *,
    comedor_ids: list[int],
    permission_code: str,
):
    if not comedor_ids:
        return []
    user_ids = (
        AccesoComedorPWA.objects.filter(
            activo=True,
            comedor_id__in=comedor_ids,
            user__is_active=True,
        )
        .values_list("user_id", flat=True)
        .distinct()
    )
    users = list(User.objects.filter(id__in=user_ids, is_active=True).order_by("id"))
    return [user for user in users if user_has_permission_code(user, permission_code)]


def notify_rendicion_revision_push(
    *,
    comunicado,
    rendicion,
    permission_code: str,
    comedor_ids: list[int],
):
    if not web_push_enabled():
        return 0

    users = _get_users_with_permission_for_project_scope(
        comedor_ids=comedor_ids,
        permission_code=permission_code,
    )
    if not users:
        return 0

    payloads_by_user_id = {}
    for user in users:
        target_comedor_id = _resolve_target_comedor_id_for_user(
            user=user,
            comedor_ids=comedor_ids,
            rendicion=rendicion,
        )
        if target_comedor_id is None:
            continue
        payloads_by_user_id[user.id] = build_rendicion_push_payload(
            comunicado=comunicado,
            rendicion=rendicion,
            target_comedor_id=target_comedor_id,
        )
    if not payloads_by_user_id:
        return 0

    sent = 0
    for subscription in PushSubscriptionPWA.objects.filter(
        user__in=users,
        activo=True,
    ).select_related("user"):
        payload = payloads_by_user_id.get(subscription.user_id)
        if payload and _send_push(subscription, payload):
            sent += 1
    return sent
