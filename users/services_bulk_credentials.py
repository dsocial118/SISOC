from __future__ import annotations

import logging
import unicodedata
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

REQUIRED_COLUMNS = ("usuario", "mail", "password")
EMAIL_SUBJECT = "SISOC - Credenciales de acceso"
TEMPLATE_FILENAME = "plantilla_credenciales_usuarios.xlsx"
SHEET_NAME = "credenciales"


@dataclass(frozen=True)
class ParsedCredentialRow:
    fila: int
    usuario: str
    mail: str
    password: str


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


def _build_header_map(headers: list[str]) -> dict[str, int]:
    header_map: dict[str, int] = {}
    for index, header in enumerate(headers):
        normalized = _normalize_header(header)
        if normalized in REQUIRED_COLUMNS and normalized not in header_map:
            header_map[normalized] = index

    missing = [column for column in REQUIRED_COLUMNS if column not in header_map]
    if missing:
        missing_text = ", ".join(missing)
        raise ValidationError(
            "El archivo debe incluir las columnas obligatorias: " f"{missing_text}."
        )

    return header_map


def _load_workbook_rows(
    uploaded_file,
) -> tuple[dict[str, int], list[ParsedCredentialRow]]:
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
        raise ValidationError("El archivo Excel está vacío.")

    headers = [_clean_cell(value) for value in rows[0]]
    header_map = _build_header_map(headers)

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
                usuario=values["usuario"],
                mail=values["mail"],
                password=values["password"],
            )
        )

    if not parsed_rows:
        raise ValidationError(
            "El archivo Excel no contiene filas con datos para procesar."
        )

    return header_map, parsed_rows


def generate_bulk_credentials_template() -> bytes:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = SHEET_NAME
    worksheet.append(list(REQUIRED_COLUMNS))

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def send_bulk_credentials_email(
    *,
    user,
    plain_password: str,
    login_url: str,
) -> None:
    context = {
        "user": user,
        "plain_password": plain_password,
        "login_url": login_url,
    }
    message = render_to_string("user/bulk_credentials_email.txt", context)
    send_mail(
        subject=EMAIL_SUBJECT,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


def _validate_row_data(row: ParsedCredentialRow) -> None:
    if not row.usuario:
        raise ValidationError("La columna usuario es obligatoria.")
    if not row.mail:
        raise ValidationError("La columna mail es obligatoria.")
    try:
        validate_email(row.mail)
    except ValidationError as exc:
        raise ValidationError("El formato del mail es inválido.") from exc
    if not row.password:
        raise ValidationError("La columna password es obligatoria.")


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


def process_bulk_credentials_file(*, uploaded_file, request=None) -> dict:
    _, rows = _load_workbook_rows(uploaded_file)
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
            _validate_row_data(row)
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
                "Fallo procesando envío masivo de credenciales. fila=%s usuario=%s",
                row.fila,
                row.usuario,
            )

        results.append(row_result)

    return {
        "summary": summary,
        "rows": results,
        "filename": getattr(uploaded_file, "name", ""),
    }
