from __future__ import annotations

import logging
import os
import signal
import smtplib
import threading
import time
import unicodedata
from contextlib import contextmanager
from dataclasses import dataclass
from io import BytesIO

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.db import transaction
from django.template.loader import render_to_string
from django.urls import reverse
from openpyxl import Workbook, load_workbook

User = get_user_model()
logger = logging.getLogger("django")

DEFAULT_BULK_CREDENTIALS_SEND_TYPE = "standard"
SHEET_NAME = "credenciales"
BULK_CREDENTIALS_EMAIL_MAX_ATTEMPTS = 2
BULK_CREDENTIALS_EMAIL_RETRY_BACKOFF_SECONDS = 1
BULK_CREDENTIALS_BATCH_TIMEOUT_BUFFER_SECONDS = 5
BULK_CREDENTIALS_MIN_SECONDS_TO_START_NEXT_ROW = 5


class BulkCredentialsEmailTimeoutError(TimeoutError):
    """Timeout controlado para cortar un intento de envio antes del timeout web."""


def _safe_positive_int(value, default: int) -> int:
    try:
        parsed = int(str(value).strip())
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _get_bulk_credentials_email_attempt_timeout_seconds() -> int:
    configured_timeout = int(getattr(settings, "EMAIL_TIMEOUT", 10) or 10)
    return max(1, configured_timeout)


def _get_bulk_credentials_batch_timeout_seconds() -> int:
    worker_timeout = _safe_positive_int(os.getenv("GUNICORN_TIMEOUT", ""), 30)
    return max(
        BULK_CREDENTIALS_MIN_SECONDS_TO_START_NEXT_ROW,
        worker_timeout - BULK_CREDENTIALS_BATCH_TIMEOUT_BUFFER_SECONDS,
    )


def _get_bulk_credentials_batch_deadline() -> float:
    return time.monotonic() + float(_get_bulk_credentials_batch_timeout_seconds())


def _get_remaining_processing_seconds(deadline: float | None) -> float | None:
    if deadline is None:
        return None
    return max(0.0, deadline - time.monotonic())


def _has_enough_batch_time(deadline: float | None) -> bool:
    remaining_seconds = _get_remaining_processing_seconds(deadline)
    if remaining_seconds is None:
        return True
    return remaining_seconds >= BULK_CREDENTIALS_MIN_SECONDS_TO_START_NEXT_ROW


def _get_batch_timeout_message() -> str:
    return (
        "Se alcanzo el tiempo maximo del lote. " "Reintente con una planilla mas chica."
    )


def _get_signal_timeout_guard_components():
    if threading.current_thread() is not threading.main_thread():
        return None

    signal_alarm = getattr(signal, "SIGALRM", None)
    timer_real = getattr(signal, "ITIMER_REAL", None)
    getitimer = getattr(signal, "getitimer", None)
    setitimer = getattr(signal, "setitimer", None)
    if (
        signal_alarm is None
        or timer_real is None
        or not callable(getitimer)
        or not callable(setitimer)
    ):
        return None

    return signal_alarm, timer_real, getitimer, setitimer


@contextmanager
def _mail_send_timeout_guard(timeout_seconds: int):
    timeout_components = _get_signal_timeout_guard_components()
    if timeout_seconds <= 0 or timeout_components is None:
        yield
        return

    signal_alarm, timer_real, getitimer, setitimer = timeout_components
    previous_handler = signal.getsignal(signal_alarm)
    previous_timer = getitimer(timer_real)

    def _raise_mail_timeout(signum, frame):  # pragma: no cover - depende de signal
        raise BulkCredentialsEmailTimeoutError(
            "Timeout enviando credenciales al servidor de correo."
        )

    signal.signal(signal_alarm, _raise_mail_timeout)
    setitimer(timer_real, float(timeout_seconds))
    try:
        yield
    finally:
        setitimer(timer_real, 0)
        signal.signal(signal_alarm, previous_handler)
        if previous_timer != (0.0, 0.0):
            setitimer(timer_real, *previous_timer)


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
        required_columns=("usuario", "mail"),
        template_headers=("usuario", "mail"),
        template_filename="plantilla_credenciales_usuarios.xlsx",
        email_subject="SISOC - Credenciales de acceso",
        email_template_name="user/bulk_credentials_email.txt",
        description=(
            "Carga un archivo .xlsx con encabezados usuario y mail. Se valida "
            "el usuario existente y se envia la credencial temporal vigente al "
            "mail informado en la planilla."
        ),
    ),
    "inet": BulkCredentialsSendTypeConfig(
        key="inet",
        label="INET",
        required_columns=("usuario", "mail", "nombre_del_centro"),
        template_headers=("usuario", "mail", "Nombre del Centro"),
        template_filename="plantilla_credenciales_usuarios_inet.xlsx",
        email_subject="Acceso a la plataforma y capacitación virtual – INET",
        email_template_name="user/bulk_credentials_email_inet.txt",
        description=(
            "Carga un archivo .xlsx con encabezados usuario, mail y Nombre "
            "del Centro. Ademas del acceso, el correo incluye la capacitacion "
            "virtual y el video de referencia para INET."
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
    try:
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
    finally:
        workbook.close()


def validate_bulk_credentials_workbook(
    uploaded_file,
    *,
    send_type: str | None = None,
) -> BulkCredentialsSendTypeConfig:
    send_type_config = get_bulk_credentials_send_type_config(send_type)
    try:
        uploaded_file.seek(0)
        workbook = load_workbook(uploaded_file, read_only=True, data_only=True)
    except Exception as exc:
        raise ValidationError("No se pudo leer el archivo Excel cargado.") from exc

    try:
        worksheet = (
            workbook[SHEET_NAME]
            if SHEET_NAME in workbook.sheetnames
            else workbook.active
        )
        rows = worksheet.iter_rows(values_only=True)
        try:
            header_row = next(rows)
        except StopIteration as exc:
            raise ValidationError("El archivo Excel esta vacio.") from exc

        headers = [_clean_cell(value) for value in header_row]
        _build_header_map(headers, send_type_config=send_type_config)

        for row in rows:
            values = [_clean_cell(value) for value in row]
            if any(values):
                uploaded_file.seek(0)
                return send_type_config

        raise ValidationError(
            "El archivo Excel no contiene filas con datos para procesar."
        )
    finally:
        workbook.close()


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


def _send_bulk_credentials_email_once(  # pylint: disable=too-many-arguments
    *,
    user,
    recipient_email: str,
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
        recipient_list=[recipient_email],
        fail_silently=False,
    )


EMAIL_ERROR_MESSAGES = (
    (
        (BulkCredentialsEmailTimeoutError, TimeoutError),
        "Timeout al comunicarse con el servidor de correo.",
    ),
    (
        smtplib.SMTPAuthenticationError,
        "El servidor de correo rechazo la autenticacion.",
    ),
    (smtplib.SMTPConnectError, "No se pudo conectar al servidor de correo."),
    (smtplib.SMTPServerDisconnected, "El servidor de correo cerro la conexion."),
    (
        smtplib.SMTPRecipientsRefused,
        "El servidor de correo rechazo el destinatario indicado.",
    ),
    (smtplib.SMTPDataError, "El servidor de correo rechazo el mensaje enviado."),
    (smtplib.SMTPException, "Ocurrio un error del servidor de correo."),
    (OSError, "Ocurrio un error de red al enviar el correo."),
)


def build_bulk_credentials_error_message(exc: Exception) -> str:
    if isinstance(exc, ValidationError):
        return " ".join(exc.messages)
    for error_types, message in EMAIL_ERROR_MESSAGES:
        if isinstance(exc, error_types):
            return message
    return "Ocurrio un error inesperado al procesar la fila."


def _build_email_retry_failure_message(last_error: Exception | None) -> str:
    base_message = build_bulk_credentials_error_message(
        last_error or ValidationError("No se pudo enviar el correo.")
    )
    return f"{base_message} El envio se reintento sin exito."


def send_bulk_credentials_email(  # pylint: disable=too-many-arguments
    *,
    user,
    recipient_email: str,
    plain_password: str,
    login_url: str,
    send_type: str | None = None,
    nombre_del_centro: str = "",
    max_total_seconds: float | None = None,
) -> None:
    timeout_seconds = _get_bulk_credentials_email_attempt_timeout_seconds()
    total_deadline = (
        time.monotonic() + max_total_seconds
        if max_total_seconds is not None and max_total_seconds > 0
        else None
    )
    last_error = None

    for attempt in range(1, BULK_CREDENTIALS_EMAIL_MAX_ATTEMPTS + 1):
        remaining_total_seconds = _get_remaining_processing_seconds(total_deadline)
        if remaining_total_seconds is not None and remaining_total_seconds < 1:
            raise ValidationError(_get_batch_timeout_message())

        attempt_timeout_seconds = timeout_seconds
        if remaining_total_seconds is not None:
            attempt_timeout_seconds = min(
                timeout_seconds,
                max(1, int(remaining_total_seconds)),
            )

        try:
            with _mail_send_timeout_guard(attempt_timeout_seconds):
                _send_bulk_credentials_email_once(
                    user=user,
                    recipient_email=recipient_email,
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
                remaining_total_seconds = _get_remaining_processing_seconds(
                    total_deadline
                )
                if (
                    remaining_total_seconds is not None
                    and remaining_total_seconds
                    <= BULK_CREDENTIALS_EMAIL_RETRY_BACKOFF_SECONDS + 1
                ):
                    break
                time.sleep(BULK_CREDENTIALS_EMAIL_RETRY_BACKOFF_SECONDS)

    raise ValidationError(
        _build_email_retry_failure_message(last_error)
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


def _get_row_recipient_email(row: ParsedCredentialRow) -> str:
    recipient_email = row.mail.strip()
    try:
        validate_email(recipient_email)
    except ValidationError as exc:
        raise ValidationError("El formato del mail es invalido.") from exc
    return recipient_email


def _get_user_plain_password(user) -> str:
    profile = getattr(user, "profile", None)
    plain_password = (
        getattr(profile, "temporary_password_plaintext", "") or ""
    ).strip()
    if not plain_password:
        raise ValidationError(
            (
                "El usuario no tiene una contraseña temporal visible para enviar. "
                "Genere o cargue una nueva contraseña temporal antes de reintentar."
            )
        )
    return plain_password


def process_bulk_credentials_row(
    *,
    row: ParsedCredentialRow,
    send_type_config: BulkCredentialsSendTypeConfig,
    login_url: str,
    max_total_seconds: float | None = None,
) -> dict[str, object]:
    _validate_row_data(row, send_type_config=send_type_config)
    with transaction.atomic():
        user = (
            User.objects.select_related("profile")
            .filter(username__iexact=row.usuario)
            .first()
        )
        if not user:
            raise ValidationError("No existe un usuario con ese nombre.")

        recipient_email = _get_row_recipient_email(row)
        plain_password = _get_user_plain_password(user)

        send_bulk_credentials_email(
            user=user,
            recipient_email=recipient_email,
            plain_password=plain_password,
            login_url=login_url,
            send_type=send_type_config.key,
            nombre_del_centro=row.nombre_del_centro,
            max_total_seconds=max_total_seconds,
        )

    return {
        "fila": row.fila,
        "usuario": row.usuario,
        "mail_destino": recipient_email,
        "estado": "enviada",
        "mensaje": "Credenciales enviadas correctamente.",
        "password_actualizada": False,
    }


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
    processing_deadline = _get_bulk_credentials_batch_deadline()

    for row_index, row in enumerate(rows):
        if not _has_enough_batch_time(processing_deadline):
            timeout_message = _get_batch_timeout_message()
            for pending_row in rows[row_index:]:
                summary["procesadas"] += 1
                summary["rechazadas"] += 1
                results.append(
                    {
                        "fila": pending_row.fila,
                        "usuario": pending_row.usuario,
                        "mail_destino": pending_row.mail,
                        "estado": "rechazada",
                        "mensaje": timeout_message,
                        "password_actualizada": False,
                    }
                )
            break

        summary["procesadas"] += 1
        row_result = {
            "fila": row.fila,
            "usuario": row.usuario,
            "mail_destino": row.mail,
            "estado": "rechazada",
            "mensaje": "",
            "password_actualizada": False,
        }

        try:
            row_result = process_bulk_credentials_row(
                row=row,
                send_type_config=send_type_config,
                login_url=login_url,
                max_total_seconds=_get_remaining_processing_seconds(
                    processing_deadline
                ),
            )
            if row_result["password_actualizada"]:
                summary["actualizadas"] += 1
            else:
                summary["sin_cambios"] += 1
            summary["enviadas"] += 1
        except ValidationError as exc:
            summary["rechazadas"] += 1
            row_result["mensaje"] = build_bulk_credentials_error_message(exc)
        except Exception as exc:
            summary["rechazadas"] += 1
            row_result["mensaje"] = build_bulk_credentials_error_message(exc)
            logger.exception(
                (
                    "Fallo procesando envio masivo de credenciales. "
                    "tipo=%s fila=%s usuario=%s"
                ),
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
