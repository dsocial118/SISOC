"""Tests para issue #1979.

Cubren:
- Usuarios sin email y con email repetido en forms.
- User import sin columna correo.
- Bulk credentials agrupado por mail destinatario.
- Nombre y apellido en el cuerpo del email.
"""

from io import BytesIO

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from openpyxl import Workbook

from users.forms import CustomUserChangeForm, UserCreationForm
from users.models import (
    BulkCredentialsJob,
    BulkCredentialsJobRow,
)
from users.services_bulk_credentials import (
    process_bulk_credentials_file,
)
from users.services_bulk_credentials_jobs import (
    create_bulk_credentials_job,
    process_bulk_credentials_job,
)
from users.services_user_import import (
    USER_IMPORT_TEMPLATE_HEADERS,
    process_single_user_import_row,
)

User = get_user_model()


def _build_excel_file(rows, headers=("usuario", "mail")):
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


def _set_visible_temporary_password(user, plain_password):
    profile = user.profile
    profile.must_change_password = True
    profile.temporary_password_plaintext = plain_password
    profile.save(update_fields=["must_change_password", "temporary_password_plaintext"])
    return user


# ---------- A1: forms permiten email vacío y repetido ----------


@pytest.mark.django_db
def test_user_creation_form_acepta_email_vacio():
    form = UserCreationForm(
        data={
            "username": "sin_email_user",
            "email": "",
            "password": "Inicial123!",
            "first_name": "Juan",
            "last_name": "Pérez",
        },
    )
    assert form.is_valid(), form.errors
    user = form.save()
    assert user.email == ""
    assert user.username == "sin_email_user"


@pytest.mark.django_db
def test_user_creation_form_acepta_email_repetido():
    User.objects.create_user(
        username="primer_usuario",
        email="repetido@example.com",
        password="Pass123!",
    )
    form = UserCreationForm(
        data={
            "username": "segundo_usuario",
            "email": "repetido@example.com",
            "password": "Pass123!",
            "first_name": "Ana",
            "last_name": "García",
        },
    )
    assert form.is_valid(), form.errors
    nuevo = form.save()
    assert nuevo.email == "repetido@example.com"
    assert User.objects.filter(email__iexact="repetido@example.com").count() == 2


@pytest.mark.django_db
def test_user_change_form_acepta_email_vacio():
    existing = User.objects.create_user(
        username="cambia_email",
        email="viejo@example.com",
        password="Pass123!",
    )
    form = CustomUserChangeForm(
        data={
            "username": "cambia_email",
            "email": "",
            "first_name": "Pedro",
            "last_name": "Lopez",
        },
        instance=existing,
    )
    assert form.is_valid(), form.errors


# ---------- A2: user import sin columna correo ----------


class _StubImportJob:
    """Job mínimo para process_single_user_import_row."""

    is_pwa_import = False
    send_credentials = False


@pytest.mark.django_db
def test_user_import_row_sin_correo_genera_username_desde_nombre():
    job = _StubImportJob()
    resultado = process_single_user_import_row(
        row_data={
            "nombre": "Ana",
            "apellido": "García",
            "correo": "",
            "permisos": "",
            "provincias": "",
            "rol": "operadora",
            "fila": 2,
        },
        job=job,
    )
    assert resultado["status"]
    # Username generado contiene el apellido normalizado
    user = User.objects.filter(first_name="Ana", last_name="García").first()
    assert user is not None
    assert user.email == ""
    assert user.username.startswith("garcia"), user.username


@pytest.mark.django_db
def test_user_import_row_email_existente_actualiza_grupos():
    from django.contrib.auth.models import Group

    grupo_nuevo = Group.objects.create(name="GrupoNuevo")
    existing = User.objects.create_user(
        username="primer.import", email="shared@example.com", password="Pass!"
    )
    job = _StubImportJob()
    resultado = process_single_user_import_row(
        row_data={
            "nombre": "Carla",
            "apellido": "Ruiz",
            "correo": "shared@example.com",
            "permisos": "GrupoNuevo",
            "provincias": "",
            "rol": "",
            "fila": 2,
        },
        job=job,
    )
    from users.models import UserImportJobRow

    assert resultado["status"] == UserImportJobRow.Status.CREATED
    assert resultado.get("mensaje", "").startswith("Usuario primer.import actualizado")
    assert User.objects.filter(email__iexact="shared@example.com").count() == 1
    assert existing.groups.filter(pk=grupo_nuevo.pk).exists()


@pytest.mark.django_db
def test_user_import_row_email_existente_sin_grupos_nuevos_marca_skipped():
    from django.contrib.auth.models import Group

    grupo = Group.objects.create(name="GrupoExistente")
    existing = User.objects.create_user(
        username="primer.import2", email="shared2@example.com", password="Pass!"
    )
    existing.groups.add(grupo)
    job = _StubImportJob()
    resultado = process_single_user_import_row(
        row_data={
            "nombre": "Carla",
            "apellido": "Ruiz",
            "correo": "shared2@example.com",
            "permisos": "GrupoExistente",
            "provincias": "",
            "rol": "",
            "fila": 3,
        },
        job=job,
    )
    from users.models import UserImportJobRow

    assert resultado["status"] == UserImportJobRow.Status.SKIPPED
    assert resultado.get("mensaje", "").startswith("Usuario primer.import2 ya existe")


def test_user_import_template_headers_incluye_correo():
    assert "Correo" in USER_IMPORT_TEMPLATE_HEADERS


# ---------- C: nombre y apellido en el email ----------


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_bulk_credentials_email_incluye_nombre_y_apellido():
    user = User.objects.create_user(
        username="con_datos",
        email="con_datos@example.com",
        password="Inicial123!",
        first_name="Lucía",
        last_name="Fernández",
    )
    _set_visible_temporary_password(user, "Inicial123!")

    upload = _build_excel_file([("con_datos", "con_datos@example.com")])
    process_bulk_credentials_file(uploaded_file=upload, send_type="standard")

    assert len(mail.outbox) == 1
    body = mail.outbox[0].body
    assert "Lucía Fernández" in body


# ---------- D: agrupamiento por destinatario ----------


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_bulk_credentials_agrupa_credenciales_por_mismo_destinatario():
    user1 = User.objects.create_user(
        username="user_uno",
        email="x@example.com",
        password="Pass1!",
        first_name="Uno",
        last_name="Apellido",
    )
    user2 = User.objects.create_user(
        username="user_dos",
        email="x@example.com",
        password="Pass2!",
        first_name="Dos",
        last_name="Apellido",
    )
    user3 = User.objects.create_user(
        username="user_solo",
        email="z@example.com",
        password="Pass3!",
        first_name="Solo",
        last_name="Otra",
    )
    _set_visible_temporary_password(user1, "Pass1!")
    _set_visible_temporary_password(user2, "Pass2!")
    _set_visible_temporary_password(user3, "Pass3!")

    upload = _build_excel_file(
        [
            ("user_uno", "compartido@example.com"),
            ("user_dos", "compartido@example.com"),
            ("user_solo", "solo@example.com"),
        ]
    )

    result = process_bulk_credentials_file(uploaded_file=upload, send_type="standard")

    # 3 filas procesadas y enviadas, pero solo 2 correos (1 agrupado + 1 solo)
    assert result["summary"]["procesadas"] == 3
    assert result["summary"]["enviadas"] == 3
    assert len(mail.outbox) == 2

    # El correo agrupado contiene ambas credenciales
    agrupado = next(msg for msg in mail.outbox if msg.to == ["compartido@example.com"])
    assert "user_uno" in agrupado.body
    assert "user_dos" in agrupado.body
    assert "Pass1!" in agrupado.body
    assert "Pass2!" in agrupado.body

    # El correo individual sólo trae sus datos
    individual = next(msg for msg in mail.outbox if msg.to == ["solo@example.com"])
    assert "user_solo" in individual.body
    assert "Pass3!" in individual.body
    assert "user_uno" not in individual.body


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_bulk_credentials_agrupa_cuando_destinatario_se_resuelve_desde_user_email():
    """Si la columna mail está vacía, se usa user.email y debe agruparse igual."""
    user1 = User.objects.create_user(
        username="vacio_uno",
        email="comp@example.com",
        password="Aaa1!",
        first_name="A",
        last_name="A",
    )
    user2 = User.objects.create_user(
        username="vacio_dos",
        email="comp@example.com",
        password="Bbb2!",
        first_name="B",
        last_name="B",
    )
    _set_visible_temporary_password(user1, "Aaa1!")
    _set_visible_temporary_password(user2, "Bbb2!")

    upload = _build_excel_file([("vacio_uno", ""), ("vacio_dos", "")])
    result = process_bulk_credentials_file(uploaded_file=upload, send_type="standard")

    assert result["summary"]["enviadas"] == 2
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["comp@example.com"]
    assert "vacio_uno" in mail.outbox[0].body
    assert "vacio_dos" in mail.outbox[0].body


# ---------- Defensivos R3: INET no agrupa con centros distintos ----------


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_inet_no_agrupa_cuando_centros_son_distintos():
    """Aunque dos filas INET compartan destinatario, no se agrupan si los
    nombres de centro difieren: evita mezclar datos en el correo."""
    user_a = User.objects.create_user(
        username="inet_a",
        email="inet_a@example.com",
        password="Pass!",
        first_name="A",
        last_name="A",
    )
    user_b = User.objects.create_user(
        username="inet_b",
        email="inet_b@example.com",
        password="Pass!",
        first_name="B",
        last_name="B",
    )
    _set_visible_temporary_password(user_a, "Pass!")
    _set_visible_temporary_password(user_b, "Pass!")

    upload = _build_excel_file(
        [
            ("inet_a", "compartido@example.com", "CFP 401"),
            ("inet_b", "compartido@example.com", "CFP 402"),
        ],
        headers=("usuario", "mail", "Nombre del Centro"),
    )
    result = process_bulk_credentials_file(uploaded_file=upload, send_type="inet")

    assert result["summary"]["enviadas"] == 2
    # Dos correos distintos al mismo destinatario, uno por centro
    assert len(mail.outbox) == 2
    assert all(msg.to == ["compartido@example.com"] for msg in mail.outbox)
    bodies = [msg.body for msg in mail.outbox]
    assert any("CFP 401" in body and "inet_a" in body for body in bodies)
    assert any("CFP 402" in body and "inet_b" in body for body in bodies)


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_inet_agrupa_cuando_centro_y_destinatario_coinciden():
    user_a = User.objects.create_user(
        username="inet_mismo_a",
        email="a@example.com",
        password="Pass!",
        first_name="A",
        last_name="A",
    )
    user_b = User.objects.create_user(
        username="inet_mismo_b",
        email="b@example.com",
        password="Pass!",
        first_name="B",
        last_name="B",
    )
    _set_visible_temporary_password(user_a, "Pass!")
    _set_visible_temporary_password(user_b, "Pass!")

    upload = _build_excel_file(
        [
            ("inet_mismo_a", "centro@example.com", "CFP 401"),
            ("inet_mismo_b", "centro@example.com", "CFP 401"),
        ],
        headers=("usuario", "mail", "Nombre del Centro"),
    )
    result = process_bulk_credentials_file(uploaded_file=upload, send_type="inet")

    assert result["summary"]["enviadas"] == 2
    assert len(mail.outbox) == 1
    body = mail.outbox[0].body
    assert "inet_mismo_a" in body
    assert "inet_mismo_b" in body
    assert "CFP 401" in body


# ---------- Defensivos R1: resume no duplica correos al destinatario ----------


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_worker_no_re_agrupa_si_destinatario_ya_recibio_envio_previo(
    settings, tmp_path
):
    """Si en un job ya hay una fila SENT con cierto destinatario y se reanuda
    con filas pendientes para el mismo destinatario, no se vuelve a agrupar:
    el destinatario ya recibió un correo, no debe recibir uno repetido con
    todas las credenciales."""
    settings.MEDIA_ROOT = tmp_path
    operator = User.objects.create_user(
        username="bulk_operator_r1",
        email="op@example.com",
        password="Pass!",
    )
    user_a = User.objects.create_user(
        username="reagr_a", email="reagr_a@x.com", password="Pass!"
    )
    user_b = User.objects.create_user(
        username="reagr_b", email="reagr_b@x.com", password="Pass!"
    )
    user_c = User.objects.create_user(
        username="reagr_c", email="reagr_c@x.com", password="Pass!"
    )
    for user in (user_a, user_b, user_c):
        _set_visible_temporary_password(user, "Pass!")

    upload = _build_excel_file(
        [
            ("reagr_a", "compartido@example.com"),
            ("reagr_b", "compartido@example.com"),
            ("reagr_c", "compartido@example.com"),
        ]
    )
    job = create_bulk_credentials_job(
        uploaded_file=upload, send_type="standard", requested_by=operator
    )
    # Simulamos que la fila 2 (reagr_a) ya fue enviada en una corrida anterior
    BulkCredentialsJobRow.objects.create(
        job=job,
        fila=2,
        usuario="reagr_a",
        mail_destino="compartido@example.com",
        status=BulkCredentialsJobRow.Status.SENT,
        password_actualizada=False,
        mensaje="OK previo",
        attempts=1,
    )
    job.next_row_index = 1
    job.sent_rows = 1
    job.unchanged_password_rows = 1
    job.processed_rows = 1
    job.save(
        update_fields=[
            "next_row_index",
            "sent_rows",
            "unchanged_password_rows",
            "processed_rows",
        ]
    )

    process_bulk_credentials_job(job)
    job.refresh_from_db()

    # No re-agrupa: reagr_b y reagr_c se envían en correos separados, no juntos.
    assert job.status == BulkCredentialsJob.Status.COMPLETED
    assert len(mail.outbox) == 2
    assert all(msg.to == ["compartido@example.com"] for msg in mail.outbox)
    # Cada correo contiene solo a su propio usuario
    body_b = next(m.body for m in mail.outbox if "reagr_b" in m.body)
    assert "reagr_c" not in body_b
    body_c = next(m.body for m in mail.outbox if "reagr_c" in m.body)
    assert "reagr_b" not in body_c


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_worker_no_agrupa_cuando_primary_tiene_attempts_previos(settings, tmp_path):
    """Si la fila primaria ya tenía attempts > 0 (resume tras fallo posible
    post-envío), debe procesarse sola para acotar duplicación al destinatario."""
    settings.MEDIA_ROOT = tmp_path
    operator = User.objects.create_user(
        username="bulk_operator_attempts",
        email="op2@example.com",
        password="Pass!",
    )
    user_a = User.objects.create_user(
        username="att_a", email="att_a@x.com", password="Pass!"
    )
    user_b = User.objects.create_user(
        username="att_b", email="att_b@x.com", password="Pass!"
    )
    _set_visible_temporary_password(user_a, "Pass!")
    _set_visible_temporary_password(user_b, "Pass!")

    upload = _build_excel_file(
        [
            ("att_a", "compartido2@example.com"),
            ("att_b", "compartido2@example.com"),
        ]
    )
    job = create_bulk_credentials_job(
        uploaded_file=upload, send_type="standard", requested_by=operator
    )
    # Fila 2 (att_a) ya fue intentada y falló: attempts = 1, status = FAILED
    BulkCredentialsJobRow.objects.create(
        job=job,
        fila=2,
        usuario="att_a",
        mail_destino="compartido2@example.com",
        status=BulkCredentialsJobRow.Status.FAILED,
        password_actualizada=False,
        mensaje="fallo previo",
        attempts=1,
    )
    job.rejected_rows = 1
    job.processed_rows = 1
    job.save(update_fields=["rejected_rows", "processed_rows"])

    process_bulk_credentials_job(job)
    job.refresh_from_db()

    # Se envían 2 correos (uno por fila), no un grupo único de 2.
    assert job.status == BulkCredentialsJob.Status.COMPLETED
    assert len(mail.outbox) == 2
    bodies = [m.body for m in mail.outbox]
    assert any("att_a" in b and "att_b" not in b for b in bodies)
    assert any("att_b" in b and "att_a" not in b for b in bodies)


# ---------- Defensivos R2: el cache evita N queries por destinatario ----------


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_recipient_cache_resuelve_destinatarios_con_una_query(
    django_assert_num_queries,
):
    """Cuando las filas no informan mail explícito, todos los emails de los
    usuarios se resuelven en una sola query, no una por fila."""
    from users.services_bulk_credentials import _build_recipient_cache
    from users.services_bulk_credentials import (
        _load_workbook_rows,
        get_bulk_credentials_send_type_config,
    )

    for index in range(5):
        User.objects.create_user(
            username=f"cache_user_{index}",
            email=f"cache_user_{index}@example.com",
            password="Pass!",
        )
    upload = _build_excel_file([(f"cache_user_{i}", "") for i in range(5)])
    config = get_bulk_credentials_send_type_config("standard")
    rows = _load_workbook_rows(upload, send_type_config=config)

    with django_assert_num_queries(1):
        cache = _build_recipient_cache(rows)

    assert len(cache) == 5
    assert cache["cache_user_0"] == "cache_user_0@example.com"
