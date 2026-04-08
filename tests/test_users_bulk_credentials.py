from io import BytesIO

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core import mail
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from django.test import RequestFactory, override_settings
from django.contrib.sessions.middleware import SessionMiddleware
from openpyxl import Workbook, load_workbook
from rest_framework.authtoken.models import Token

from users.forms import BulkCredentialsUploadForm
from users.services_bulk_credentials import (
    BulkCredentialsEmailTimeoutError,
    process_bulk_credentials_file,
)
from users.services import UsuariosService
from users.views import BulkCredentialsTemplateView, BulkCredentialsUploadView

User = get_user_model()


def _build_excel_file(rows, headers=("usuario", "mail", "password")):
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "credenciales"
    worksheet.append(list(headers))
    for row in rows:
        worksheet.append(list(row))

    output = BytesIO()
    workbook.save(output)
    return SimpleUploadedFile(
        "credenciales.xlsx",
        output.getvalue(),
        content_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    )


def _bulk_credentials_permission():
    content_type = ContentType.objects.get_for_model(Group)
    permission, _ = Permission.objects.get_or_create(
        content_type=content_type,
        codename="role_enviar_credenciales_masivas",
        defaults={"name": "Enviar credenciales masivas"},
    )
    return permission


def _build_request(method: str, path: str, user, *, data=None, files=None):
    factory = RequestFactory()
    request_method = getattr(factory, method.lower())
    request = request_method(path, data=data or {})
    SessionMiddleware(lambda req: None).process_request(request)
    request.session.save()
    setattr(request, "_messages", FallbackStorage(request))
    request.user = user
    if files:
        request.FILES.update(files)
    return request


@pytest.mark.django_db
def test_bulk_credentials_template_download_requires_both_permissions():
    user = User.objects.create_user(
        username="users_bulk_reader",
        email="reader@example.com",
        password="Secreta123!",
    )
    change_user_permission = Permission.objects.get(
        content_type__app_label="auth",
        codename="change_user",
    )
    user.user_permissions.add(change_user_permission)

    with pytest.raises(PermissionDenied):
        BulkCredentialsTemplateView.as_view()(
            _build_request("get", "/usuarios/credenciales-masivas/plantilla/", user),
        )

    user.user_permissions.add(_bulk_credentials_permission())
    user = User.objects.get(pk=user.pk)
    response = BulkCredentialsTemplateView.as_view()(
        _build_request("get", "/usuarios/credenciales-masivas/plantilla/", user),
    )

    assert response.status_code == 200
    assert (
        response["Content-Type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    workbook = load_workbook(BytesIO(response.content))
    worksheet = workbook.active
    header = [cell.value for cell in next(worksheet.iter_rows(max_row=1))]
    assert header == ["usuario", "mail", "password"]


@pytest.mark.django_db
def test_bulk_credentials_template_download_supports_inet_template():
    user = User.objects.create_superuser(
        username="users_bulk_inet_template",
        email="inet-template@example.com",
        password="Secreta123!",
    )

    response = BulkCredentialsTemplateView.as_view()(
        _build_request(
            "get",
            "/usuarios/credenciales-masivas/plantilla/",
            user,
            data={"tipo_envio": "inet"},
        ),
    )

    assert response.status_code == 200
    assert (
        response["Content-Disposition"]
        == 'attachment; filename="plantilla_credenciales_usuarios_inet.xlsx"'
    )
    workbook = load_workbook(BytesIO(response.content))
    worksheet = workbook.active
    header = [cell.value for cell in next(worksheet.iter_rows(max_row=1))]
    assert header == ["usuario", "mail", "password", "Nombre del Centro"]


@pytest.mark.django_db
@override_settings(ROOT_URLCONF="tests.urls_users_bulk_credentials")
def test_user_list_context_shows_bulk_credentials_button_only_with_role_permission(
    mocker,
):
    user = User.objects.create_user(
        username="users_bulk_button",
        email="button@example.com",
        password="Secreta123!",
    )
    mocker.patch(
        "users.services.build_columns_context",
        return_value={"table_headers": [], "table_fields": []},
    )
    view_user_permission = Permission.objects.get(
        content_type__app_label="auth",
        codename="view_user",
    )
    change_user_permission = Permission.objects.get(
        content_type__app_label="auth",
        codename="change_user",
    )
    user.user_permissions.add(view_user_permission, change_user_permission)

    request = _build_request("get", "/usuarios/", user)
    context = UsuariosService.get_usuarios_list_context(request)
    assert context["additional_buttons"] == []

    user.user_permissions.add(_bulk_credentials_permission())
    user = User.objects.get(pk=user.pk)
    request = _build_request("get", "/usuarios/", user)
    context = UsuariosService.get_usuarios_list_context(request)
    assert context["additional_buttons"] == [
        {
            "label": "ENVIO DE CREDENCIALES",
            "url": "/usuarios/credenciales-masivas/",
            "class": "btn btn-lg btn-export-csv",
            "title": "Actualizar password y enviar credenciales desde Excel",
        }
    ]


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_process_bulk_credentials_updates_password_and_sends_to_mail_from_excel():
    user = User.objects.create_user(
        username="bulk_target",
        email="viejo@example.com",
        password="Vieja123!",
    )
    Token.objects.create(user=user)

    upload = _build_excel_file(
        [("bulk_target", "nuevo@example.com", "Nueva123!")],
    )

    result = process_bulk_credentials_file(
        uploaded_file=upload,
        send_type="standard",
    )

    user.refresh_from_db()
    profile = user.profile
    assert result["summary"] == {
        "procesadas": 1,
        "enviadas": 1,
        "actualizadas": 1,
        "sin_cambios": 0,
        "rechazadas": 0,
    }
    assert result["rows"][0]["estado"] == "enviada"
    assert result["rows"][0]["mail_destino"] == "nuevo@example.com"
    assert result["rows"][0]["password_actualizada"] is True
    assert user.email == "viejo@example.com"
    assert user.check_password("Nueva123!") is True
    assert profile.must_change_password is True
    assert profile.password_changed_at is None
    assert profile.password_reset_requested_at is None
    assert profile.temporary_password_plaintext == "Nueva123!"
    assert Token.objects.filter(user=user).exists() is False
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["nuevo@example.com"]


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_process_bulk_credentials_same_data_sends_email_without_updating():
    user = User.objects.create_user(
        username="bulk_same",
        email="same@example.com",
        password="Misma123!",
    )

    upload = _build_excel_file(
        [("bulk_same", "same@example.com", "Misma123!")],
    )

    result = process_bulk_credentials_file(
        uploaded_file=upload,
        send_type="standard",
    )

    user.refresh_from_db()
    assert result["summary"] == {
        "procesadas": 1,
        "enviadas": 1,
        "actualizadas": 0,
        "sin_cambios": 1,
        "rechazadas": 0,
    }
    assert result["rows"][0]["mail_destino"] == "same@example.com"
    assert result["rows"][0]["password_actualizada"] is False
    assert user.email == "same@example.com"
    assert user.check_password("Misma123!") is True
    assert len(mail.outbox) == 1


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_process_bulk_credentials_rejects_unknown_user_and_continues():
    known_user = User.objects.create_user(
        username="bulk_known",
        email="known@example.com",
        password="Inicial123!",
    )
    upload = _build_excel_file(
        [
            ("missing_user", "missing@example.com", "Temporal123!"),
            ("bulk_known", "known@example.com", "Inicial123!"),
        ],
    )

    result = process_bulk_credentials_file(
        uploaded_file=upload,
        send_type="standard",
    )

    known_user.refresh_from_db()
    assert result["summary"] == {
        "procesadas": 2,
        "enviadas": 1,
        "actualizadas": 0,
        "sin_cambios": 1,
        "rechazadas": 1,
    }
    assert result["rows"][0]["estado"] == "rechazada"
    assert "No existe un usuario" in result["rows"][0]["mensaje"]
    assert result["rows"][1]["estado"] == "enviada"
    assert known_user.email == "known@example.com"
    assert len(mail.outbox) == 1


@pytest.mark.django_db
def test_process_bulk_credentials_rejects_missing_required_headers():
    upload = _build_excel_file(
        [("bulk_user", "user@example.com", "Temporal123!")],
        headers=("usuario", "mail"),
    )

    with pytest.raises(ValidationError) as exc:
        process_bulk_credentials_file(uploaded_file=upload, send_type="standard")

    assert "columnas obligatorias" in " ".join(exc.value.messages)


@pytest.mark.django_db
def test_process_bulk_credentials_rejects_missing_inet_center_column():
    upload = _build_excel_file(
        [("bulk_user", "user@example.com", "Temporal123!")],
        headers=("usuario", "mail", "password"),
    )

    with pytest.raises(ValidationError) as exc:
        process_bulk_credentials_file(uploaded_file=upload, send_type="inet")

    assert "nombre_del_centro" in " ".join(exc.value.messages)


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_process_bulk_credentials_reports_missing_mail_and_continues():
    User.objects.create_user(
        username="bulk_invalid",
        email="bulk_invalid@example.com",
        password="Temporal123!",
    )
    User.objects.create_user(
        username="bulk_valid",
        email="bulk_valid@example.com",
        password="Temporal123!",
    )
    upload = _build_excel_file(
        [
            ("bulk_invalid", "", "Temporal123!"),
            ("bulk_valid", "destino@example.com", "Temporal123!"),
        ],
    )

    result = process_bulk_credentials_file(
        uploaded_file=upload,
        send_type="standard",
    )

    assert result["summary"] == {
        "procesadas": 2,
        "enviadas": 1,
        "actualizadas": 0,
        "sin_cambios": 1,
        "rechazadas": 1,
    }
    assert "mail es obligatoria" in result["rows"][0]["mensaje"]
    assert result["rows"][0]["mail_destino"] == ""
    assert result["rows"][1]["estado"] == "enviada"
    assert result["rows"][1]["mail_destino"] == "destino@example.com"
    assert len(mail.outbox) == 1


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_process_bulk_credentials_allows_shared_recipient_email():
    first_user = User.objects.create_user(
        username="bulk_shared_one",
        email="one@example.com",
        password="Inicial123!",
    )
    second_user = User.objects.create_user(
        username="bulk_shared_two",
        email="two@example.com",
        password="Inicial123!",
    )
    upload = _build_excel_file(
        [
            ("bulk_shared_one", "shared@example.com", "NuevaOne123!"),
            ("bulk_shared_two", "shared@example.com", "NuevaTwo123!"),
        ],
    )

    result = process_bulk_credentials_file(
        uploaded_file=upload,
        send_type="standard",
    )

    first_user.refresh_from_db()
    second_user.refresh_from_db()
    assert result["summary"] == {
        "procesadas": 2,
        "enviadas": 2,
        "actualizadas": 2,
        "sin_cambios": 0,
        "rechazadas": 0,
    }
    assert first_user.email == "one@example.com"
    assert second_user.email == "two@example.com"
    assert first_user.check_password("NuevaOne123!") is True
    assert second_user.check_password("NuevaTwo123!") is True
    assert [email.to for email in mail.outbox] == [
        ["shared@example.com"],
        ["shared@example.com"],
    ]


@pytest.mark.django_db
def test_process_bulk_credentials_rolls_back_row_when_email_send_fails(mocker):
    user = User.objects.create_user(
        username="bulk_rollback",
        email="rollback@example.com",
        password="Inicial123!",
    )
    Token.objects.create(user=user)
    original_password = user.password
    mocker.patch(
        "users.services_bulk_credentials.send_bulk_credentials_email",
        side_effect=RuntimeError("smtp down"),
    )
    upload = _build_excel_file(
        [("bulk_rollback", "nuevo_rollback@example.com", "TemporalNueva123!")],
    )

    result = process_bulk_credentials_file(
        uploaded_file=upload,
        send_type="standard",
    )

    user.refresh_from_db()
    profile = user.profile
    assert result["summary"] == {
        "procesadas": 1,
        "enviadas": 0,
        "actualizadas": 0,
        "sin_cambios": 0,
        "rechazadas": 1,
    }
    assert user.email == "rollback@example.com"
    assert user.password == original_password
    assert user.check_password("Inicial123!") is True
    assert profile.temporary_password_plaintext is None
    assert Token.objects.filter(user=user).exists() is True


@pytest.mark.django_db
def test_process_bulk_credentials_retries_email_timeout_and_succeeds(mocker):
    user = User.objects.create_user(
        username="bulk_retry",
        email="retry@example.com",
        password="Inicial123!",
    )
    send_once = mocker.patch(
        "users.services_bulk_credentials._send_bulk_credentials_email_once",
        side_effect=[BulkCredentialsEmailTimeoutError("smtp timeout"), None],
    )
    sleep = mocker.patch("users.services_bulk_credentials.time.sleep")
    upload = _build_excel_file(
        [("bulk_retry", "retry@example.com", "Inicial123!")],
    )

    result = process_bulk_credentials_file(
        uploaded_file=upload,
        send_type="standard",
    )

    assert result["summary"] == {
        "procesadas": 1,
        "enviadas": 1,
        "actualizadas": 0,
        "sin_cambios": 1,
        "rechazadas": 0,
    }
    assert result["rows"][0]["estado"] == "enviada"
    assert send_once.call_count == 2
    sleep.assert_called_once()


@pytest.mark.django_db
def test_process_bulk_credentials_rejects_row_when_email_timeout_persists(mocker):
    user = User.objects.create_user(
        username="bulk_timeout",
        email="timeout@example.com",
        password="Inicial123!",
    )
    Token.objects.create(user=user)
    original_password = user.password
    send_once = mocker.patch(
        "users.services_bulk_credentials._send_bulk_credentials_email_once",
        side_effect=BulkCredentialsEmailTimeoutError("smtp timeout"),
    )
    sleep = mocker.patch("users.services_bulk_credentials.time.sleep")
    upload = _build_excel_file(
        [("bulk_timeout", "timeout@example.com", "TemporalNueva123!")],
    )

    result = process_bulk_credentials_file(
        uploaded_file=upload,
        send_type="standard",
    )

    user.refresh_from_db()
    profile = user.profile
    assert result["summary"] == {
        "procesadas": 1,
        "enviadas": 0,
        "actualizadas": 0,
        "sin_cambios": 0,
        "rechazadas": 1,
    }
    assert (
        result["rows"][0]["mensaje"]
        == "No se pudo enviar el correo para esta fila luego de reintentar."
    )
    assert send_once.call_count == 2
    sleep.assert_called_once()
    assert user.password == original_password
    assert user.check_password("Inicial123!") is True
    assert profile.temporary_password_plaintext is None
    assert Token.objects.filter(user=user).exists() is True


@pytest.mark.django_db
@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    ROOT_URLCONF="tests.urls_users_bulk_credentials",
)
def test_bulk_credentials_upload_view_processes_file_and_shows_summary():
    user = User.objects.create_user(
        username="bulk_operator",
        email="operator@example.com",
        password="Secreta123!",
    )
    target = User.objects.create_user(
        username="bulk_view_target",
        email="view_target@example.com",
        password="Inicial123!",
    )
    change_user_permission = Permission.objects.get(
        content_type__app_label="auth",
        codename="change_user",
    )
    user.user_permissions.add(change_user_permission, _bulk_credentials_permission())

    upload = _build_excel_file(
        [("bulk_view_target", "nuevo_view_target@example.com", "NuevaView123!")]
    )
    form = BulkCredentialsUploadForm(
        data={"tipo_envio": "standard"},
        files={"archivo": upload},
    )
    assert form.is_valid(), form.errors

    request = _build_request(
        "post",
        "/usuarios/credenciales-masivas/",
        user,
        data={"tipo_envio": "standard"},
        files={"archivo": upload},
    )
    view = BulkCredentialsUploadView()
    view.setup(request)
    captured_context = {}

    def _fake_render_to_response(context, **kwargs):
        captured_context.update(context)
        return HttpResponse("ok")

    view.render_to_response = _fake_render_to_response

    response = view.form_valid(form)

    target.refresh_from_db()
    assert response.status_code == 200
    assert captured_context["results"]["summary"]["enviadas"] == 1
    assert captured_context["results"]["rows"][0]["estado"] == "enviada"
    assert target.email == "view_target@example.com"
    assert target.check_password("NuevaView123!") is True
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["nuevo_view_target@example.com"]


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_process_bulk_credentials_inet_uses_inet_email_template():
    user = User.objects.create_user(
        username="bulk_inet",
        email="inet-old@example.com",
        password="ViejaInet123!",
    )
    upload = _build_excel_file(
        [("bulk_inet", "inet-new@example.com", "NuevaInet123!", "CFP INET 401")],
        headers=("usuario", "mail", "password", "Nombre del Centro"),
    )

    result = process_bulk_credentials_file(
        uploaded_file=upload,
        send_type="inet",
    )

    user.refresh_from_db()
    assert result["summary"] == {
        "procesadas": 1,
        "enviadas": 1,
        "actualizadas": 1,
        "sin_cambios": 0,
        "rechazadas": 0,
    }
    assert result["send_type"] == "inet"
    assert result["send_type_label"] == "INET"
    assert user.email == "inet-old@example.com"
    assert len(mail.outbox) == 1
    assert (
        mail.outbox[0].subject == "Acceso a la plataforma y capacitación virtual – INET"
    )
    assert mail.outbox[0].to == ["inet-new@example.com"]
    assert "CFP INET 401" in mail.outbox[0].body
    assert (
        "Capacitacion a instituciones de FP para beneficiarios de VAT (1)"
        in mail.outbox[0].body
    )
    assert "En todas se abordaran los mismos temas." in mail.outbox[0].body
    assert "https://youtu.be/vR_lODbOdJg" in mail.outbox[0].body
    assert "Nos vemos pronto." in mail.outbox[0].body
