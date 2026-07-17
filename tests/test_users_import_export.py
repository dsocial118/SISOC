import csv
from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core import mail
from django.test import override_settings
from django.urls import reverse

from users.models import UserImportJob, UserImportJobRow
from users.services_user_import import send_user_import_job_credentials

User = get_user_model()


@pytest.mark.django_db
@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    ENVIRONMENT="prd",
    DOMINIO="sisoc.secretarianaf.gob.ar",
)
def test_user_import_pwa_credentials_email_uses_mobile_login_url():
    operator = User.objects.create_user(username="import_operator")
    imported_user = User.objects.create_user(
        username="pwa_user",
        email="pwa@example.com",
        first_name="PWA",
        last_name="User",
    )
    imported_user.profile.must_change_password = True
    imported_user.profile.temporary_password_plaintext = "Temporal123"
    imported_user.profile.save(
        update_fields=["must_change_password", "temporary_password_plaintext"]
    )
    job = UserImportJob.objects.create(
        requested_by=operator,
        original_filename="usuarios.xlsx",
        is_pwa_import=True,
        send_credentials=True,
    )
    UserImportJobRow.objects.create(
        job=job,
        created_user=imported_user,
        fila=2,
        email=imported_user.email,
        status=UserImportJobRow.Status.CREATED,
    )

    send_user_import_job_credentials(job)

    assert len(mail.outbox) == 1
    assert "https://sisoc.secretarianaf.gob.ar/mobile/login" in mail.outbox[0].body


@pytest.mark.django_db
@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    ENVIRONMENT="prd",
    DOMINIO="sisoc.secretarianaf.gob.ar",
)
def test_user_import_web_credentials_email_keeps_web_login_url():
    operator = User.objects.create_user(username="import_operator_web")
    imported_user = User.objects.create_user(
        username="web_user",
        email="web@example.com",
    )
    imported_user.profile.must_change_password = True
    imported_user.profile.temporary_password_plaintext = "Temporal123"
    imported_user.profile.save(
        update_fields=["must_change_password", "temporary_password_plaintext"]
    )
    job = UserImportJob.objects.create(
        requested_by=operator,
        original_filename="usuarios.xlsx",
        send_credentials=True,
    )
    UserImportJobRow.objects.create(
        job=job,
        created_user=imported_user,
        fila=2,
        email=imported_user.email,
        status=UserImportJobRow.Status.CREATED,
    )

    send_user_import_job_credentials(job)

    assert len(mail.outbox) == 1
    assert "https://sisoc.secretarianaf.gob.ar/" in mail.outbox[0].body
    assert "/mobile/login" not in mail.outbox[0].body


@pytest.mark.django_db
def test_user_import_job_download_exports_only_created_users_with_temp_password(client):
    operator = User.objects.create_user(username="import_operator")
    operator.user_permissions.add(
        Permission.objects.get(content_type__app_label="auth", codename="add_user")
    )
    created_user = User.objects.create_user(
        username="ana.garcia",
        email="ana@example.com",
        first_name="Ana",
        last_name="García",
    )
    created_user.profile.must_change_password = True
    created_user.profile.temporary_password_plaintext = "Temporal123"
    created_user.profile.save(
        update_fields=["must_change_password", "temporary_password_plaintext"]
    )
    job = UserImportJob.objects.create(
        requested_by=operator,
        original_filename="usuarios.xlsx",
    )
    UserImportJobRow.objects.create(
        job=job,
        created_user=created_user,
        fila=2,
        nombre="Ana",
        apellido="García",
        email="ana@example.com",
        rol="Operadora",
        status=UserImportJobRow.Status.CREATED,
    )
    UserImportJobRow.objects.create(
        job=job,
        fila=3,
        nombre="Omitido",
        status=UserImportJobRow.Status.SKIPPED,
    )
    client.force_login(operator)

    response = client.get(
        reverse("usuarios_importar_descargar_csv", kwargs={"pk": job.pk})
    )

    assert response.status_code == 200
    assert response["Content-Type"] == "text/csv; charset=utf-8"
    assert f"lote-usuarios-{job.pk}.csv" in response["Content-Disposition"]
    assert list(csv.reader(StringIO(response.content.decode("utf-8-sig")))) == [
        ["Usuario", "Nombre", "Apellido", "Correo", "Rol", "Contraseña temporal"],
        ["ana.garcia", "Ana", "García", "ana@example.com", "Operadora", "Temporal123"],
    ]
    detail_response = client.get(
        reverse("usuarios_importar_detalle", kwargs={"pk": job.pk})
    )
    assert detail_response.status_code == 200
    assert reverse(
        "usuarios_importar_descargar_csv", kwargs={"pk": job.pk}
    ) in detail_response.content.decode()


@pytest.mark.django_db
def test_user_import_job_download_is_not_available_to_another_operator(client):
    owner = User.objects.create_user(username="import_owner")
    other_operator = User.objects.create_user(username="other_operator")
    other_operator.user_permissions.add(
        Permission.objects.get(content_type__app_label="auth", codename="add_user")
    )
    job = UserImportJob.objects.create(
        requested_by=owner,
        original_filename="usuarios.xlsx",
    )
    client.force_login(other_operator)

    response = client.get(
        reverse("usuarios_importar_descargar_csv", kwargs={"pk": job.pk})
    )

    assert response.status_code == 404
