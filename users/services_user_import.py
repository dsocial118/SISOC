from __future__ import annotations

import logging
import unicodedata
from io import BytesIO

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.db import transaction
from django.template.loader import render_to_string
from openpyxl import Workbook, load_workbook

from django.urls import reverse

from core.models import Provincia
from users.models import ProfileTerritorialScope, UserImportJob, UserImportJobRow
from users.services_auth import generate_temporary_password_for_user

User = get_user_model()
logger = logging.getLogger("django")

USER_IMPORT_CREDENTIALS_EMAIL_TEMPLATE = "user/bulk_credentials_email.txt"
USER_IMPORT_CREDENTIALS_EMAIL_SUBJECT = "SISOC - Credenciales de acceso"
USER_IMPORT_TEMPLATE_FILENAME = "plantilla_importacion_usuarios.xlsx"
USER_IMPORT_SHEET_NAME = "usuarios"
USER_IMPORT_REQUIRED_COLUMNS = (
    "nombre",
    "apellido",
    "correo",
    "permisos",
    "provincias",
    "rol",
)
USER_IMPORT_TEMPLATE_HEADERS = (
    "Nombre",
    "Apellido",
    "Correo",
    "Permisos",
    "Provincias",
    "Rol",
)
USERNAME_MAX_LENGTH = 150


def _build_login_url() -> str:
    try:
        path = reverse("login")
    except Exception:
        path = "/"
    domain = (
        str(settings.DOMINIO).replace("http://", "").replace("https://", "").rstrip("/")
    )
    scheme = "https" if settings.ENVIRONMENT == "prd" else "http"
    return f"{scheme}://{domain}{path}"


def _normalize_header(value: object) -> str:
    text = str(value or "").strip()
    normalized = unicodedata.normalize("NFKD", text)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
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
        candidate = f"{base[:USERNAME_MAX_LENGTH - len(suffix)]}{suffix}"
        if not User.objects.filter(username__iexact=candidate).exists():
            return candidate
        counter += 1


def _parse_semicolon_field(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


def _get_active_worksheet(workbook):
    if USER_IMPORT_SHEET_NAME in workbook.sheetnames:
        return workbook[USER_IMPORT_SHEET_NAME]
    return workbook.active


def validate_user_import_workbook(uploaded_file) -> None:
    try:
        uploaded_file.seek(0)
        workbook = load_workbook(uploaded_file, read_only=True, data_only=True)
    except Exception as exc:
        raise ValidationError("No se pudo leer el archivo Excel cargado.") from exc

    try:
        worksheet = _get_active_worksheet(workbook)
        rows = worksheet.iter_rows(values_only=True)
        try:
            header_row = next(rows)
        except StopIteration as exc:
            raise ValidationError("El archivo Excel esta vacio.") from exc

        headers = [_normalize_header(v) for v in header_row]
        missing = [col for col in USER_IMPORT_REQUIRED_COLUMNS if col not in headers]
        if missing:
            raise ValidationError(
                f"El archivo debe incluir las columnas obligatorias: {', '.join(missing)}."
            )

        for row in rows:
            if any(_clean_cell(v) for v in row):
                uploaded_file.seek(0)
                return

        raise ValidationError(
            "El archivo Excel no contiene filas con datos para procesar."
        )
    finally:
        workbook.close()


def load_user_import_rows(uploaded_file) -> list[dict]:
    uploaded_file.seek(0)
    workbook = load_workbook(uploaded_file, read_only=True, data_only=True)
    try:
        worksheet = _get_active_worksheet(workbook)
        raw_rows = list(worksheet.iter_rows(values_only=True))
        if not raw_rows:
            return []

        headers = [_normalize_header(v) for v in raw_rows[0]]
        col_map = {
            col: idx
            for idx, col in enumerate(headers)
            if col in USER_IMPORT_REQUIRED_COLUMNS
        }

        parsed = []
        for row_number, row in enumerate(raw_rows[1:], start=2):
            values = {
                col: _clean_cell(row[idx] if idx < len(row) else "")
                for col, idx in col_map.items()
            }
            if not any(values.values()):
                continue
            values["fila"] = row_number
            parsed.append(values)

        return parsed
    finally:
        workbook.close()


def create_user_import_job(
    *,
    uploaded_file,
    requested_by,
    send_credentials: bool,
) -> UserImportJob:
    validate_user_import_workbook(uploaded_file)
    rows = load_user_import_rows(uploaded_file)

    job = UserImportJob(
        requested_by=requested_by,
        original_filename=getattr(uploaded_file, "name", "usuarios.xlsx"),
        send_credentials=send_credentials,
        total_rows=len(rows),
    )
    uploaded_file.seek(0)
    job.archivo.save(job.original_filename, uploaded_file, save=False)
    job.save()

    UserImportJobRow.objects.bulk_create(
        [
            UserImportJobRow(
                job=job,
                fila=row["fila"],
                nombre=row.get("nombre", ""),
                apellido=row.get("apellido", ""),
                email=row.get("correo", ""),
                rol=row.get("rol", ""),
                status=UserImportJobRow.Status.PENDING,
            )
            for row in rows
        ]
    )

    return job


def _enviar_credenciales_import(*, user, password: str) -> bool:
    if not user.email:
        return False
    try:
        context = {
            "user": user,
            "plain_password": password,
            "login_url": _build_login_url(),
        }
        message = render_to_string(USER_IMPORT_CREDENTIALS_EMAIL_TEMPLATE, context)
        send_mail(
            subject=USER_IMPORT_CREDENTIALS_EMAIL_SUBJECT,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception:
        logger.exception(
            "Fallo enviando credenciales de importacion user_id=%s", user.id
        )
        return False


def process_single_user_import_row(*, row_data: dict, job: UserImportJob) -> dict:
    nombre = row_data.get("nombre", "").strip()
    apellido = row_data.get("apellido", "").strip()
    email_raw = row_data.get("correo", "").strip()
    permisos_raw = row_data.get("permisos", "").strip()
    provincias_raw = row_data.get("provincias", "").strip()
    rol = row_data.get("rol", "").strip()

    if not email_raw:
        raise ValidationError("El campo Correo es obligatorio.")
    try:
        validate_email(email_raw)
    except ValidationError as exc:
        raise ValidationError(
            f"El correo '{email_raw}' no tiene formato valido."
        ) from exc

    email = email_raw.lower()

    if User.objects.filter(email__iexact=email).exists():
        return {
            "status": UserImportJobRow.Status.SKIPPED,
            "mensaje": f"Ya existe un usuario con el correo {email}.",
        }

    grupos = []
    for nombre_grupo in _parse_semicolon_field(permisos_raw):
        grupo = Group.objects.filter(name=nombre_grupo).first()
        if grupo is None:
            raise ValidationError(f"El grupo '{nombre_grupo}' no existe en el sistema.")
        grupos.append(grupo)

    provincias_objs = []
    for nombre_prov in _parse_semicolon_field(provincias_raw):
        prov = Provincia.objects.filter(nombre__iexact=nombre_prov).first()
        if prov is None:
            raise ValidationError(
                f"La provincia '{nombre_prov}' no existe en el sistema."
            )
        provincias_objs.append(prov)

    username = _generar_username_unico(_slug_base_desde_email(email))

    with transaction.atomic():
        user = User(
            username=username,
            email=email,
            first_name=nombre,
            last_name=apellido,
            is_staff=True,
            is_active=True,
        )
        user.set_unusable_password()
        user.save()

        if grupos:
            user.groups.set(grupos)

        profile = user.profile
        profile.rol = rol
        if provincias_objs:
            profile.es_usuario_provincial = True
        profile.save(update_fields=["rol", "es_usuario_provincial"])

        for prov in provincias_objs:
            scope_key = ProfileTerritorialScope.build_scope_key(prov.pk)
            ProfileTerritorialScope.objects.get_or_create(
                profile=profile,
                scope_key=scope_key,
                defaults={
                    "provincia_id": prov.pk,
                    "municipio": None,
                    "localidad": None,
                },
            )

        password = generate_temporary_password_for_user(user=user)

    if job.send_credentials:
        _enviar_credenciales_import(user=user, password=password)

    return {
        "status": UserImportJobRow.Status.CREATED,
        "mensaje": f"Usuario {username} creado correctamente.",
        "email": email,
    }


def build_user_import_error_message(exc: Exception) -> str:
    if isinstance(exc, ValidationError):
        return " ".join(exc.messages)
    return "Ocurrio un error inesperado al procesar la fila."


def generate_user_import_template() -> bytes:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = USER_IMPORT_SHEET_NAME
    worksheet.append(list(USER_IMPORT_TEMPLATE_HEADERS))
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()
