from __future__ import annotations

import logging
from datetime import timedelta
from typing import Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework.authtoken.models import Token

from users.services_pwa import is_pwa_user

from users.profile_utils import get_profile_or_none

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
        scheme = getattr(settings, "DEFAULT_SCHEME", "http")

    return f"{scheme}://{domain}{path}"


def send_password_reset_link(*, user, reset_link: str) -> None:
    context = {
        "user": user,
        "reset_link": reset_link,
    }
    subject = "SISOC - Restablecer contraseÃƒÂ±a"
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


def request_password_reset_for_username(*, username: str) -> None:
    normalized_username = (username or "").strip()
    if not normalized_username:
        return

    user = (
        User.objects.filter(username__iexact=normalized_username, is_active=True)
        .select_related("profile")
        .first()
    )
    if not user or not is_pwa_user(user):
        return

    profile = getattr(user, "profile", None)
    if not profile:
        return

    profile.password_reset_requested_at = timezone.now()
    profile.save(update_fields=["password_reset_requested_at"])
    logger.info("Password reset mobile solicitado user_id=%s", user.id)


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

    profile = get_profile_or_none(user)
    if profile:
        profile.must_change_password = False
        profile.password_changed_at = timezone.now()
        profile.initial_password_expires_at = None
        profile.password_reset_requested_at = None
        profile.temporary_password_plaintext = None
        profile.save(
            update_fields=[
                "must_change_password",
                "password_changed_at",
                "initial_password_expires_at",
                "password_reset_requested_at",
                "temporary_password_plaintext",
            ]
        )

    logger.info("Password reset confirmado user_id=%s", user.id)
    return user


def change_password_for_authenticated_user(*, user, new_password: str) -> User:
    """Actualiza la contraseÃƒÂ±a del usuario autenticado y limpia flags de primer ingreso."""
    user.set_password(new_password)
    user.save(update_fields=["password"])

    profile = getattr(user, "profile", None)
    if profile:
        profile.must_change_password = False
        profile.password_changed_at = timezone.now()
        profile.initial_password_expires_at = None
        profile.password_reset_requested_at = None
        profile.temporary_password_plaintext = None
        profile.save(
            update_fields=[
                "must_change_password",
                "password_changed_at",
                "initial_password_expires_at",
                "password_reset_requested_at",
                "temporary_password_plaintext",
            ]
        )

    logger.info("Password change autenticado confirmado user_id=%s", user.id)
    return user


def generate_temporary_password_for_user(*, user) -> str:
    """Genera una nueva contraseÃƒÂ±a temporal para un usuario y obliga cambio en primer login."""
    temporary_password = get_random_string(12)
    user.set_password(temporary_password)
    user.save(update_fields=["password"])

    profile = getattr(user, "profile", None)
    if profile:
        profile.must_change_password = True
        profile.password_changed_at = None
        profile.initial_password_expires_at = timezone.now() + timedelta(
            hours=settings.INITIAL_PASSWORD_MAX_AGE_HOURS
        )
        profile.password_reset_requested_at = None
        profile.temporary_password_plaintext = temporary_password
        profile.save(
            update_fields=[
                "must_change_password",
                "password_changed_at",
                "initial_password_expires_at",
                "password_reset_requested_at",
                "temporary_password_plaintext",
            ]
        )

    Token.objects.filter(user=user).delete()
    logger.info("Password temporal regenerado user_id=%s", user.id)
    return temporary_password
