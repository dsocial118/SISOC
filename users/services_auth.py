from __future__ import annotations

import logging
from typing import Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

User = get_user_model()
logger = logging.getLogger("django")


def get_user_by_uid(uidb64: str):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        return User.objects.get(pk=uid)
    except Exception:  # pragma: no cover - branch defensiva
        return None


def build_password_reset_link(*, user, request=None) -> str:
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    path = reverse(
        "password_reset_confirm",
        kwargs={"uidb64": uid, "token": token},
    )
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


def send_password_reset_link(*, user, reset_link: str) -> None:
    context = {
        "user": user,
        "reset_link": reset_link,
    }
    subject = "SISOC - Restablecer contraseña"
    message = render_to_string("user/password_reset_email.txt", context)

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


def request_password_reset_for_email(*, email: str, request=None) -> None:
    normalized_email = (email or "").strip()
    if not normalized_email:
        return

    users = User.objects.filter(
        email__iexact=normalized_email, is_active=True
    ).order_by("id")
    for user in users:
        if not user.email:
            logger.info(
                "Password reset omitido por usuario sin email. user_id=%s",
                user.id,
            )
            continue

        reset_link = build_password_reset_link(user=user, request=request)
        try:
            send_password_reset_link(user=user, reset_link=reset_link)
            logger.info("Password reset solicitado user_id=%s", user.id)
        except Exception:  # pragma: no cover - depende de backend externo
            logger.exception("Fallo enviando password reset user_id=%s", user.id)


def confirm_password_reset(
    *, uid: str, token: str, new_password: str
) -> Optional[User]:
    user = get_user_by_uid(uid)
    if not user:
        return None

    if not default_token_generator.check_token(user, token):
        return None

    user.set_password(new_password)
    user.save(update_fields=["password"])

    profile = getattr(user, "profile", None)
    if profile:
        profile.must_change_password = False
        profile.password_changed_at = timezone.now()
        profile.initial_password_expires_at = None
        profile.temporary_password_plaintext = None
        profile.save(
            update_fields=[
                "must_change_password",
                "password_changed_at",
                "initial_password_expires_at",
                "temporary_password_plaintext",
            ]
        )

    logger.info("Password reset confirmado user_id=%s", user.id)
    return user
