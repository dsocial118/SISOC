"""Service genérico para generar usuarios delegados desde una entidad.

Reutilizable por cualquier app (CDI hoy; Organización/Comedor a futuro): la app
provee el grupo fijo a asignar, un callback que vincula el usuario creado a su
entidad y, opcionalmente, un chequeo de límite. La validación de delegación
reutiliza el alcance efectivo de delegación de grupos.
"""

from __future__ import annotations

import logging
import unicodedata
from dataclasses import dataclass
from typing import Callable, Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.db import transaction
from django.template.loader import render_to_string
from django.urls import reverse

from users.services_auth import generate_temporary_password_for_user
from users.services_delegation import effective_delegatable_group_ids

User = get_user_model()
logger = logging.getLogger("django")

CREDENTIALS_EMAIL_TEMPLATE = "user/bulk_credentials_email.txt"
CREDENTIALS_EMAIL_SUBJECT = "SISOC - Credenciales de acceso"
USERNAME_MAX_LENGTH = 150


@dataclass
class DatosUsuarioDelegado:
    """Datos precargados del referente para el alta del usuario."""

    first_name: str = ""
    last_name: str = ""
    email: str = ""


def _normalizar_email(value: str) -> str:
    return (value or "").strip()


def _slug_base_desde_email(email: str) -> str:
    local_part = email.split("@", 1)[0]
    normalized = unicodedata.normalize("NFKD", local_part)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    cleaned = "".join(ch if ch.isalnum() else "." for ch in normalized.lower())
    cleaned = ".".join(part for part in cleaned.split(".") if part)
    return cleaned[:USERNAME_MAX_LENGTH] or "usuario"


def _generar_username_unico(base: str) -> str:
    if not User.objects.filter(username__iexact=base).exists():
        return base

    counter = 2
    while True:
        suffix = f"-{counter}"
        candidate = f"{base[: USERNAME_MAX_LENGTH - len(suffix)]}{suffix}"
        if not User.objects.filter(username__iexact=candidate).exists():
            return candidate
        counter += 1


def _actor_puede_delegar_grupo(actor, grupo: Group) -> bool:
    if actor is None or not getattr(actor, "is_authenticated", False):
        return False
    if actor.is_superuser:
        return True
    return grupo.pk in effective_delegatable_group_ids(actor)


def _build_login_url(request=None) -> str:
    try:
        path = reverse("login")
    except Exception:  # pragma: no cover - defensiva
        path = "/"
    if request is not None:
        scheme = "https" if request.is_secure() else "http"
        domain = request.get_host()
    else:
        domain = (
            str(settings.DOMINIO)
            .replace("http://", "")
            .replace("https://", "")
            .rstrip("/")
        )
        scheme = "https" if settings.ENVIRONMENT == "prd" else "http"
    return f"{scheme}://{domain}{path}"


def _validar_email(datos: DatosUsuarioDelegado) -> str:
    email = _normalizar_email(datos.email)
    if not email:
        raise ValidationError(
            "El email del referente es obligatorio para generar el usuario."
        )
    try:
        validate_email(email)
    except ValidationError as exc:
        raise ValidationError("El email del referente no es válido.") from exc
    return email


def _enviar_credenciales(*, user, password: str, request=None) -> bool:
    """Envía las credenciales por mail. Best-effort: loguea y no propaga."""
    if not user.email:
        return False
    from users.services_bulk_credentials import (  # noqa: PLC0415
        BulkCredentialEntry,
    )

    entry = BulkCredentialEntry(
        username=user.username,
        plain_password=password,
        first_name=user.first_name or "",
        last_name=user.last_name or "",
    )
    context = {
        "entries": [entry],
        "is_grouped": False,
        "user_username": entry.username,
        "user_full_name": entry.full_name,
        "plain_password": password,
        "nombre_del_centro": "",
        "login_url": _build_login_url(request=request),
    }
    message = render_to_string(CREDENTIALS_EMAIL_TEMPLATE, context)
    try:
        send_mail(
            subject=CREDENTIALS_EMAIL_SUBJECT,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception:  # pragma: no cover - depende de backend externo
        logger.exception(
            "Fallo enviando credenciales del usuario delegado user_id=%s",
            user.id,
        )
        return False


def generar_usuario_delegado(  # pylint: disable=too-many-arguments
    *,
    actor,
    datos: DatosUsuarioDelegado,
    grupo_nombre: str,
    vinculo_callback: Callable[[User], None],
    limite_check: Optional[Callable[[], bool]] = None,
    request=None,
) -> dict:
    """Crea un usuario con grupo fijo, lo vincula a una entidad y envía credenciales.

    Args:
        actor: usuario que ejecuta la acción; debe poder delegar `grupo_nombre`.
        datos: nombre/apellido/email precargados del referente.
        grupo_nombre: grupo fijo a asignar (no editable por el flujo).
        vinculo_callback: asocia el usuario creado a su entidad (CDI/Org/...).
        limite_check: si se provee y devuelve False, se rechaza la creación.
        request: opcional, para construir la URL de login del mail.

    Returns:
        dict con `user`, `password` (temporal en claro) y `email_enviado`.

    Raises:
        ValidationError ante grupo inexistente, actor sin delegación,
        límite alcanzado o email inválido/duplicado.
    """
    grupo = Group.objects.filter(name=grupo_nombre).first()
    if grupo is None:
        raise ValidationError(
            f"El grupo «{grupo_nombre}» no existe. "
            "Ejecute la semilla/sincronización de grupos."
        )

    if not _actor_puede_delegar_grupo(actor, grupo):
        raise ValidationError("No tiene permisos para asignar el grupo requerido.")

    if limite_check is not None and not limite_check():
        raise ValidationError(
            "Se alcanzó el máximo de usuarios permitidos para esta entidad."
        )

    email = _validar_email(datos)
    username = _generar_username_unico(_slug_base_desde_email(email))

    with transaction.atomic():
        user = User(
            username=username,
            email=email,
            first_name=(datos.first_name or "").strip(),
            last_name=(datos.last_name or "").strip(),
            is_staff=True,
            is_active=True,
        )
        user.set_unusable_password()
        user.save()  # el signal post_save crea el Profile

        user.groups.set([grupo])

        password = generate_temporary_password_for_user(user=user)

        vinculo_callback(user)

    email_enviado = _enviar_credenciales(user=user, password=password, request=request)

    logger.info(
        "Usuario delegado creado user_id=%s grupo=%s actor_id=%s email_enviado=%s",
        user.id,
        grupo_nombre,
        getattr(actor, "id", None),
        email_enviado,
    )
    return {
        "user": user,
        "password": password,
        "email_enviado": email_enviado,
    }
