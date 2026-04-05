from io import StringIO

import pytest
from django.contrib.auth.models import Group, User
from django.core.management import call_command
from openpyxl import Workbook


pytestmark = pytest.mark.django_db


def _build_excel_file(tmp_path, rows):
    workbook = Workbook()
    worksheet = workbook.active
    for row in rows:
        worksheet.append(row)
    file_path = tmp_path / "usuarios_vat.xlsx"
    workbook.save(file_path)
    return file_path


def test_import_vat_cfp_users_from_excel_creates_and_updates_users(tmp_path, settings):
    settings.INITIAL_PASSWORD_MAX_AGE_HOURS = 24
    file_path = _build_excel_file(
        tmp_path,
        [
            ["Usuario", "Email", "Nombre completo", "Apellido", "Contraseña"],
            ["cfp-001", "cfp-001@example.com", "Ana", "Paz", "Clave123"],
            ["cfp-002", "cfp-002@example.com", "Bruno Lopez", "", "Clave456"],
        ],
    )

    existing_user = User.objects.create_user(
        username="cfp-001",
        email="anterior@example.com",
        password="oldpass",
    )

    out = StringIO()
    call_command("import_vat_cfp_users", str(file_path), stdout=out)

    existing_user.refresh_from_db()
    imported_user = User.objects.get(username="cfp-002")
    cfp_group = Group.objects.get(name="CFP")

    assert existing_user.email == "cfp-001@example.com"
    assert existing_user.profile.rol == "CFP"
    assert existing_user.profile.must_change_password is True
    assert existing_user.profile.temporary_password_plaintext == "Clave123"
    assert existing_user.groups.filter(pk=cfp_group.pk).exists()
    assert cfp_group.permissions.filter(codename="role_referentecentrovat").exists()

    assert existing_user.last_name == "CFP"
    assert imported_user.first_name == "Bruno"
    assert imported_user.last_name == "CFP"
    assert imported_user.profile.temporary_password_plaintext == "Clave456"
    assert imported_user.groups.filter(pk=cfp_group.pk).exists()

    output = out.getvalue()
    assert "Procesados: 2" in output
    assert "creados: 1" in output
    assert "actualizados: 1" in output


def test_import_vat_cfp_users_dry_run_does_not_persist_changes(tmp_path):
    file_path = _build_excel_file(
        tmp_path,
        [
            ["Usuario", "Email", "Nombre", "Apellido"],
            ["cfp-dry", "cfp-dry@example.com", "Maria", "Sosa"],
        ],
    )

    out = StringIO()
    call_command(
        "import_vat_cfp_users",
        str(file_path),
        "--default-password=Temporal123",
        "--dry-run",
        stdout=out,
    )

    assert not User.objects.filter(username="cfp-dry").exists()
    assert not Group.objects.filter(name="CFP").exists()
    assert "Simulación finalizada" in out.getvalue()


def test_import_vat_cfp_users_generates_short_username_from_nombre(tmp_path):
    file_path = _build_excel_file(
        tmp_path,
        [
            ["Nombre", "Email", "Contraseña"],
            [
                "Escuela Municipal De Formación Profesional Nº 1 Crucero Gral. Belgrano - Dipregep N°7469",
                "cfp-belgrano@example.com",
                "Clave123",
            ],
            [
                "Centro De Formación Profesional (C.F.P.) Nº 02",
                "cfp-02@example.com",
                "Clave456",
            ],
        ],
    )

    call_command("import_vat_cfp_users", str(file_path), stdout=StringIO())

    usernames = set(User.objects.values_list("username", flat=True))

    assert "escmunformnpro1" in usernames
    assert "ctrformnprocfp02" in usernames


def test_import_vat_cfp_users_with_only_nombre_generates_fantasy_email(tmp_path):
    file_path = _build_excel_file(
        tmp_path,
        [
            ["Nombre"],
            ["Centro Ceja Tafi Del Valle"],
            ["Centro De Formación Laboral Nº 1"],
        ],
    )

    call_command(
        "import_vat_cfp_users",
        str(file_path),
        "--default-password=1",
        stdout=StringIO(),
    )

    user_one = User.objects.get(username="ctrcejatafivall")
    user_two = User.objects.get(username="ctrformnlab1")

    assert user_one.email == "ctrcejatafivall@vat.local"
    assert user_two.email == "ctrformnlab1@vat.local"
    assert user_one.last_name == "CFP"
    assert user_two.last_name == "CFP"
    assert user_one.profile.temporary_password_plaintext == "1"
    assert user_two.profile.temporary_password_plaintext == "1"


def test_import_vat_cfp_users_reuses_generated_username_on_second_run(tmp_path):
    file_path = _build_excel_file(
        tmp_path,
        [
            ["Nombre"],
            ["Centro Ceja Tafi Del Valle"],
        ],
    )

    call_command(
        "import_vat_cfp_users",
        str(file_path),
        "--default-password=1",
        stdout=StringIO(),
    )
    call_command(
        "import_vat_cfp_users",
        str(file_path),
        "--default-password=1",
        stdout=StringIO(),
    )

    assert User.objects.filter(username="ctrcejatafivall").count() == 1


def test_import_vat_cfp_users_avoids_colliding_with_existing_user(tmp_path):
    file_path = _build_excel_file(
        tmp_path,
        [
            ["Nombre"],
            ["Escuela Municipal De Formación Profesional Nº 1 Crucero Gral. Belgrano"],
        ],
    )

    User.objects.create_user(
        username="escmunformnpro1",
        email="otro@example.com",
        password="previa",
    )

    call_command(
        "import_vat_cfp_users",
        str(file_path),
        "--default-password=1",
        stdout=StringIO(),
    )

    imported_user = User.objects.get(email="escmunformnpro11@vat.local")

    assert imported_user.username == "escmunformnpro11"
