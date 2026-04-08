from __future__ import annotations

import logging
import signal
import smtplib
import threading
import time
import unicodedata
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import timedelta
from io import BytesIO

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.db import transaction
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from openpyxl import Workbook, load_workbook
from rest_framework.authtoken.models import Token

from users.models import Profile

User = get_user_model()
logger = logging.getLogger("django")

DEFAULT_BULK_CREDENTIALS_SEND_TYPE = "standard"
SHEET_NAME = "credenciales"
BULK_CREDENTIALS_EMAIL_MAX_ATTEMPTS = 2
BULK_CREDENTIALS_EMAIL_RETRY_BACKOFF_SECONDS = 1


class BulkCredentialsEmailTimeoutError(TimeoutError):
    """Timeout controlado para cortar un intento de envio antes del timeout web."""


def _get_bulk_credentials_email_attempt_timeout_seconds() -> int:
    configured_timeout = int(getattr(settings, "EMAIL_TIMEOUT", 10) or 10)
    return max(1, configured_timeout)


def _supports_signal_timeout_guard() -> bool:
    return (
        threading.current_thread() is threading.main_thread()
        and hasattr(signal, "SIGALRM")
        and hasattr(signal, "ITIMER_REAL")
        and hasattr(signal, "getitimer")
        and hasattr(signal, "setitimer")
    )


@contextmanager
def _mail_send_timeout_guard(timeout_seconds: int):
    if timeout_seconds <= 0 or not _supports_signal_timeout_guard():
        yield
        return

    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_timer = signal.getitimer(signal.ITIMER_REAL)

    def _raise_mail_timeout(signum, frame):  # pragma: no cover - depende de signal
        raise BulkCredentialsEmailTimeoutError(
            "Timeout enviando credenciales al servidor de correo."
        )

    signal.signal(signal.SIGALRM, _raise_mail_timeout)
    signal.setitimer(signal.ITIMER_REAL, float(timeout_seconds))
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        if previous_timer != (0.0, 0.0):
            signal.setitimer(signal.ITIMER_REAL, *previous_timer)


@dataclass(frozen=True)
class BulkCredentialsSendTypeConfig:
    key: str
    label: str
    required_columns: tuple[str, ...]
    template_headers: tuple[str, ...]
    template_filename: str
    email_subject: str
    email_template_name: str
    description: str


@dataclass(frozen=True)
class ParsedCredentialRow:
    fila: int
    data: dict[str, str]

    @property
    def usuario(self) -> str:
        return self.data.get("usuario", "")

    @property
    def mail(self) -> str:
        return self.data.get("mail", "")

    @property
    def password(self) -> str:
        return self.data.get("password", "")

    @property
    def nombre_del_centro(self) -> str:
        return self.data.get("nombre_del_centro", "")


BULK_CREDENTIALS_SEND_TYPES = {
    "standard": BulkCredentialsSendTypeConfig(
        key="standard",
        label="Estandar",
        required_columns=("usuario", "mail", "password"),
        template_headers=("usuario", "mail", "password"),
        template_filename="plantilla_credenciales_usuarios.xlsx",
        email_subject="SISOC - Credenciales de acceso",
        email_template_name="user/bulk_credentials_email.txt",
        description=(
            "Carga un archivo .xlsx con encabezados usuario, mail y password. "
            "Se valida el usuario existente, se sincronizan los datos vigentes "
            "y luego se envia el correo de credenciales."
        ),
    ),
    "inet": BulkCredentialsSendTypeConfig(
        key="inet",
        label="INET",
        required_columns=("usuario", "mail", "password", "nombre_del_centro"),
        template_headers=("usuario", "mail", "password", "Nombre del Centro"),
        template_filename="plantilla_credenciales_usuarios_inet.xlsx",
        email_subject="Acceso a la plataforma y capacitación virtual – INET",
        email_template_name="user/bulk_credentials_email_inet.txt",
        description=(
            "Carga un archivo .xlsx con encabezados usuario, mail, password y "
            "Nombre del Centro. Ademas del acceso, el correo incluye la "
            "capacitacion virtual y el video de referencia para INET."
        ),
    ),
}


def _normalize_header(value: object) -> str:
    text = str(value or "").strip()
    normalized = unicodedata.normalize("NFKD", text)
    normalized = "".join(
        character for character in normalized if not unicodedata.combining(character)
    )
    normalized = normalized.lower().replace(" ", "_").replace("-", "_")
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    return normalized.strip("_")


def _clean_cell(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def get_bulk_credentials_send_type_config(
    send_type: str | None = None,
) -> BulkCredentialsSendTypeConfig:
    normalized_send_type = (
        str(send_type or DEFAULT_BULK_CREDENTIALS_SEND_TYPE).strip().lower()
    )
    config = BULK_CREDENTIALS_SEND_TYPES.get(normalized_send_type)
    if not config:
        raise ValidationError("El tipo de envio seleccionado no es valido.")
    return config


def get_bulk_credentials_send_type_choices() -> list[tuple[str, str]]:
    return [
        (config.key, config.label) for config in BULK_CREDENTIALS_SEND_TYPES.values()
    ]


def get_bulk_credentials_send_type_contexts() -> list[dict[str, object]]:
    contexts = []
    for config in BULK_CREDENTIALS_SEND_TYPES.values():
        contexts.append(
            {
                "key": config.key,
                "label": config.label,
                "required_columns": config.template_headers,
                "description": config.description,
            }
        )
    return contexts


def _build_login_url(*, request=None) -> str:
    try:
        path = reverse("login")
    except Exception:
        login_setting = str(getattr(settings, "LOGIN_URL", "") or "").strip()
        path = login_setting if login_setting.startswith("/") else "/"
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


def _build_header_map(
    headers: list[str],
    *,
    send_type_config: BulkCredentialsSendTypeConfig,
) -> dict[str, int]:
    header_map: dict[str, int] = {}
    for index, header in enumerate(headers):
        normalized = _normalize_header(header)
        if (
            normalized in send_type_config.required_columns
            and normalized not in header_map
        ):
            header_map[normalized] = index

    missing = [
        column
        for column in send_type_config.required_columns
        if column not in header_map
    ]
    if missing:
        missing_text = ", ".join(missing)
        raise ValidationError(
            "El archivo debe incluir las columnas obligatorias: " f"{missing_text}."
        )

    return header_map


def _load_workbook_rows(
    uploaded_file,
    *,
    send_type_config: BulkCredentialsSendTypeConfig,
) -> list[ParsedCredentialRow]:
    try:
        uploaded_file.seek(0)
        workbook = load_workbook(uploaded_file, read_only=True, data_only=True)
    except Exception as exc:
        raise ValidationError("No se pudo leer el archivo Excel cargado.") from exc

    if SHEET_NAME in workbook.sheetnames:
        worksheet = workbook[SHEET_NAME]
    else:
        worksheet = workbook.active
    rows = list(worksheet.iter_rows(values_only=True))
    if not rows:
        raise ValidationError("El archivo Excel esta vacio.")

    headers = [_clean_cell(value) for value in rows[0]]
    header_map = _build_header_map(headers, send_type_config=send_type_config)

    parsed_rows: list[ParsedCredentialRow] = []
    for row_number, row in enumerate(rows[1:], start=2):
        values = {
            column: _clean_cell(row[index] if index < len(row) else "")
            for column, index in header_map.items()
        }
        if not any(values.values()):
            continue

        parsed_rows.append(
            ParsedCredentialRow(
                fila=row_number,
                data=values,
            )
        )

    if not parsed_rows:
        raise ValidationError(
            "El archivo Excel no contiene filas con datos para procesar."
        )

    return parsed_rows


def generate_bulk_credentials_template(send_type: str | None = None) -> bytes:
    send_type_config = get_bulk_credentials_send_type_config(send_type)
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = SHEET_NAME
    worksheet.append(list(send_type_config.template_headers))

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def get_bulk_credentials_template_filename(send_type: str | None = None) -> str:
    send_type_config = get_bulk_credentials_send_type_config(send_type)
    return send_type_config.template_filename


def _send_bulk_credentials_email_once(
    *,
    user,
    plain_password: str,
    login_url: str,
    send_type: str | None = None,
    nombre_del_centro: str = "",
) -> None:
    send_type_config = get_bulk_credentials_send_type_config(send_type)
    context = {
        "user": user,
        "plain_password": plain_password,
        "login_url": login_url,
        "nombre_del_centro": nombre_del_centro,
    }
    message = render_to_string(send_type_config.email_template_name, context)
    send_mail(
        subject=send_type_config.email_subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


def send_bulk_credentials_email(
    *,
    user,
    plain_password: str,
    login_url: str,
    send_type: str | None = None,
    nombre_del_centro: str = "",
) -> None:
    timeout_seconds = _get_bulk_credentials_email_attempt_timeout_seconds()
    last_error = None

    for attempt in range(1, BULK_CREDENTIALS_EMAIL_MAX_ATTEMPTS + 1):
        try:
            with _mail_send_timeout_guard(timeout_seconds):
                _send_bulk_credentials_email_once(
                    user=user,
                    plain_password=plain_password,
                    login_url=login_url,
                    send_type=send_type,
                    nombre_del_centro=nombre_del_centro,
                )
            return
        except (
            BulkCredentialsEmailTimeoutError,
            TimeoutError,
            smtplib.SMTPException,
            OSError,
        ) as exc:
            last_error = exc
            logger.warning(
                (
                    "Fallo enviando credenciales por correo. "
                    "usuario=%s intento=%s/%s tipo=%s"
                ),
                user.username,
                attempt,
                BULK_CREDENTIALS_EMAIL_MAX_ATTEMPTS,
                send_type or DEFAULT_BULK_CREDENTIALS_SEND_TYPE,
                exc_info=True,
            )
            if attempt < BULK_CREDENTIALS_EMAIL_MAX_ATTEMPTS:
                time.sleep(BULK_CREDENTIALS_EMAIL_RETRY_BACKOFF_SECONDS)

    raise ValidationError(
        "No se pudo enviar el correo para esta fila luego de reintentar."
    ) from last_error


def _validate_row_data(
    row: ParsedCredentialRow,
    *,
    send_type_config: BulkCredentialsSendTypeConfig,
) -> None:
    for column in send_type_config.required_columns:
        if row.data.get(column):
            continue
        raise ValidationError(f"La columna {column} es obligatoria.")

    try:
        validate_email(row.mail)
    except ValidationError as exc:
        raise ValidationError("El formato del mail es invalido.") from exc


def _validate_unique_email(*, user, email: str) -> None:
    if not email:
        return

    duplicated = User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists()
    if duplicated:
        raise ValidationError("Ya existe otro usuario con ese mail.")


def _update_password_state(*, user, plain_password: str) -> None:
    user.set_password(plain_password)
    user.save(update_fields=["password"])

    profile, _ = Profile.objects.get_or_create(user=user)
    profile.must_change_password = True
    profile.password_changed_at = None
    profile.initial_password_expires_at = timezone.now() + timedelta(
        hours=settings.INITIAL_PASSWORD_MAX_AGE_HOURS
    )
    profile.password_reset_requested_at = None
    profile.temporary_password_plaintext = plain_password
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


def process_bulk_credentials_file(
    *,
    uploaded_file,
    send_type: str | None = None,
    request=None,
) -> dict:
    send_type_config = get_bulk_credentials_send_type_config(send_type)
    rows = _load_workbook_rows(
        uploaded_file,
        send_type_config=send_type_config,
    )
    results: list[dict[str, object]] = []
    summary = {
        "procesadas": 0,
        "enviadas": 0,
        "actualizadas": 0,
        "sin_cambios": 0,
        "rechazadas": 0,
    }
    login_url = _build_login_url(request=request)

    for row in rows:
        summary["procesadas"] += 1
        row_result = {
            "fila": row.fila,
            "usuario": row.usuario,
            "estado": "rechazada",
            "mensaje": "",
            "email_actualizado": False,
            "password_actualizada": False,
        }

        try:
            _validate_row_data(row, send_type_config=send_type_config)
            with transaction.atomic():
                user = (
                    User.objects.select_related("profile")
                    .filter(username__iexact=row.usuario)
                    .first()
                )
                if not user:
                    raise ValidationError("No existe un usuario con ese nombre.")

                _validate_unique_email(user=user, email=row.mail)

                email_updated = False
                password_updated = False

                if user.email != row.mail:
                    user.email = row.mail
                    user.save(update_fields=["email"])
                    email_updated = True

                if not user.check_password(row.password):
                    _update_password_state(user=user, plain_password=row.password)
                    password_updated = True

                send_bulk_credentials_email(
                    user=user,
                    plain_password=row.password,
                    login_url=login_url,
                    send_type=send_type_config.key,
                    nombre_del_centro=row.nombre_del_centro,
                )

                row_result["email_actualizado"] = email_updated
                row_result["password_actualizada"] = password_updated
                row_result["estado"] = "enviada"
                row_result["mensaje"] = "Credenciales enviadas correctamente."

                if email_updated or password_updated:
                    summary["actualizadas"] += 1
                else:
                    summary["sin_cambios"] += 1

                summary["enviadas"] += 1
        except ValidationError as exc:
            summary["rechazadas"] += 1
            row_result["mensaje"] = " ".join(exc.messages)
        except Exception:
            summary["rechazadas"] += 1
            row_result["mensaje"] = "No se pudo enviar el correo para esta fila."
            logger.exception(
                "Fallo procesando envio masivo de credenciales. tipo=%s fila=%s usuario=%s",
                send_type_config.key,
                row.fila,
                row.usuario,
            )

        results.append(row_result)

    return {
        "summary": summary,
        "rows": results,
        "filename": getattr(uploaded_file, "name", ""),
        "send_type": send_type_config.key,
        "send_type_label": send_type_config.label,
    }
