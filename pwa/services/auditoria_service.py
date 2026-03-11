import logging
import uuid

from pwa.models import AuditoriaSesionPWA
from users.services_pwa import get_pwa_context

LOGGER = logging.getLogger(__name__)


def registrar_evento_auth(
    *,
    request,
    evento: str,
    resultado: str,
    user=None,
    username_intentado: str | None = None,
    codigo_respuesta: int | None = None,
    motivo_error: str | None = None,
    session_id: uuid.UUID | None = None,
):
    """Registra eventos de autenticación y contexto PWA sin interrumpir flujo principal."""
    try:
        contexto = get_pwa_context(user) if user else {}
        rol_pwa_snapshot = contexto.get("roles", []) or []
        comedor_ids = set(contexto.get("comedores_representados", []) or [])
        comedor_operador_id = contexto.get("comedor_operador_id")
        if comedor_operador_id:
            comedor_ids.add(comedor_operador_id)

        AuditoriaSesionPWA.objects.create(
            user=user if getattr(user, "is_authenticated", False) else None,
            username_intentado=username_intentado,
            evento=evento,
            resultado=resultado,
            ip=_get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:512] or None,
            path=request.path[:255],
            metodo_http=request.method[:10],
            codigo_respuesta=codigo_respuesta,
            motivo_error=(motivo_error or "")[:255] or None,
            session_id=session_id or uuid.uuid4(),
            rol_pwa_snapshot=rol_pwa_snapshot,
            comedor_ids_snapshot=sorted(comedor_ids),
            app_version=(request.META.get("HTTP_X_APP_VERSION", "")[:50] or None),
            platform=(request.META.get("HTTP_X_PLATFORM", "")[:30] or None),
            is_standalone=_parse_optional_bool(request.META.get("HTTP_X_PWA_STANDALONE")),
        )
    except Exception:  # pragma: no cover - no bloquear login por auditoría
        LOGGER.exception("Error registrando auditoría de sesión PWA")


def _get_client_ip(request) -> str | None:
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip() or None
    return request.META.get("REMOTE_ADDR") or None


def _parse_optional_bool(raw_value) -> bool | None:
    if raw_value is None:
        return None
    normalized = str(raw_value).strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return None
