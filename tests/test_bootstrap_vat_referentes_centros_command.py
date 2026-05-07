from io import StringIO

import pytest
from django.contrib.auth.models import Group, User
from django.core.management import call_command
from openpyxl import Workbook

from VAT.models import Centro
from core.models import Localidad, Municipio, Provincia


pytestmark = pytest.mark.django_db


def _build_excel_file(tmp_path, filename, rows):
    workbook = Workbook()
    worksheet = workbook.active
    for row in rows:
        worksheet.append(row)
    file_path = tmp_path / filename
    workbook.save(file_path)
    return file_path


def test_bootstrap_vat_referentes_centros_creates_and_assigns_by_row_order(tmp_path):
    provincia = Provincia.objects.create(id=2, nombre="Buenos Aires")
    municipio = Municipio.objects.create(
        id=92,
        nombre="General Pueyrredon",
        provincia=provincia,
    )
    Localidad.objects.create(id=3085, nombre="Mar del Plata", municipio=municipio)

    users_file = _build_excel_file(
        tmp_path,
        "usuarios.xlsx",
        [
            ["nombre"],
            ["Escuela Municipal De Formación Profesional Nº 1 Crucero Gral. Belgrano"],
            ["Centro C. E. J. A. Adultos N° 3"],
        ],
    )
    centers_file = _build_excel_file(
        tmp_path,
        "centros.xlsx",
        [
            [
                "nombre",
                "codigo",
                "provincia_id",
                "municipio_id",
                "localidad_id",
                "domicilio_actividad",
                "tipo_gestion",
                "clase_institucion",
                "situacion",
            ],
            [
                "Escuela Municipal De Formación Profesional Nº 1 Crucero Gral. Belgrano",
                "616126000",
                "2",
                "92",
                "3085",
                "SAN MARTIN 5420",
                "Estatal",
                "Formación Profesional",
                "Institución de ETP",
            ],
            [
                "Centro C. E. J. A. Adultos N° 3",
                "900001800",
                "2",
                "92",
                "3085",
                "SARGENTO CABRAL 576",
                "Estatal",
                "Formación Profesional",
                "Institución de Otro Nivel y/o Modalidad",
            ],
        ],
    )

    call_command(
        "bootstrap_vat_referentes_centros",
        str(users_file),
        str(centers_file),
        "--default-password=1",
        stdout=StringIO(),
    )

    group = Group.objects.get(name="CFP")
    first_user = User.objects.get(username="cfp1crucbelg")
    second_user = User.objects.get(username="ceja3")
    first_center = Centro.objects.get(codigo="616126000")
    second_center = Centro.objects.get(codigo="900001800")

    assert first_user.groups.filter(pk=group.pk).exists()
    assert second_user.groups.filter(pk=group.pk).exists()
    assert first_center.referente_id == first_user.id
    assert list(first_center.referentes.values_list("pk", flat=True)) == [first_user.id]
    assert second_center.referente_id == second_user.id
    assert list(second_center.referentes.values_list("pk", flat=True)) == [
        second_user.id
    ]


def test_bootstrap_vat_referentes_centros_overwrite_replaces_referentes_set(tmp_path):
    provincia = Provincia.objects.create(id=2, nombre="Buenos Aires")
    municipio = Municipio.objects.create(id=92, nombre="La Plata", provincia=provincia)
    localidad = Localidad.objects.create(id=3085, nombre="Tolosa", municipio=municipio)
    group, _ = Group.objects.get_or_create(name="CFP")
    old_user = User.objects.create_user(username="cfp-old", password="1")
    extra_user = User.objects.create_user(username="cfp-extra", password="1")
    old_user.groups.add(group)
    extra_user.groups.add(group)
    centro = Centro.objects.create(
        nombre="Centro Existente",
        codigo="616126000",
        provincia=provincia,
        municipio=municipio,
        localidad=localidad,
        domicilio_actividad="Calle 1",
        telefono="221111111",
        celular="221222222",
        correo="centro@vat.test",
        nombre_referente="Ana",
        apellido_referente="Perez",
        telefono_referente="221333333",
        correo_referente="ana@vat.test",
        referente=old_user,
        tipo_gestion="Estatal",
        clase_institucion="Formacion Profesional",
        situacion="Institucion de ETP",
    )
    centro.referentes.add(old_user, extra_user)
    users_file = _build_excel_file(
        tmp_path,
        "usuarios.xlsx",
        [["nombre"], ["Centro Nuevo Reemplazo"]],
    )
    centers_file = _build_excel_file(
        tmp_path,
        "centros.xlsx",
        [
            ["nombre", "codigo", "tipo_gestion", "clase_institucion", "situacion"],
            [
                "Centro Existente",
                "616126000",
                "Estatal",
                "Formacion Profesional",
                "Institucion de ETP",
            ],
        ],
    )

    call_command(
        "bootstrap_vat_referentes_centros",
        str(users_file),
        str(centers_file),
        "--default-password=1",
        "--overwrite",
        stdout=StringIO(),
    )

    centro.refresh_from_db()
    assert centro.referente_id not in {old_user.id, extra_user.id}
    assert list(centro.referentes.values_list("pk", flat=True)) == [centro.referente_id]


def test_bootstrap_vat_referentes_centros_dry_run_only_validates(tmp_path):
    users_file = _build_excel_file(
        tmp_path,
        "usuarios.xlsx",
        [["nombre"], ["Centro Ceja Tafi Del Valle"]],
    )
    centers_file = _build_excel_file(
        tmp_path,
        "centros.xlsx",
        [
            ["nombre", "codigo", "tipo_gestion", "clase_institucion", "situacion"],
            [
                "Centro Ceja Tafi Del Valle",
                "900157700",
                "Estatal",
                "Formación Profesional",
                "Institución de Otro Nivel y/o Modalidad",
            ],
        ],
    )

    out = StringIO()
    call_command(
        "bootstrap_vat_referentes_centros",
        str(users_file),
        str(centers_file),
        "--default-password=1",
        "--dry-run",
        stdout=out,
    )

    assert not User.objects.filter(email__endswith="@vat.local").exists()
    assert not Centro.objects.filter(codigo="900157700").exists()
    assert "Simulación finalizada" in out.getvalue()


def test_bootstrap_vat_referentes_centros_requires_same_row_count(tmp_path):
    users_file = _build_excel_file(
        tmp_path,
        "usuarios.xlsx",
        [
            ["nombre"],
            ["Centro Ceja Tafi Del Valle"],
            ["Centro De Formación Laboral Nº 1"],
        ],
    )
    centers_file = _build_excel_file(
        tmp_path,
        "centros.xlsx",
        [
            ["nombre", "codigo", "tipo_gestion", "clase_institucion", "situacion"],
            [
                "Centro Ceja Tafi Del Valle",
                "900157700",
                "Estatal",
                "Formación Profesional",
                "Institución de Otro Nivel y/o Modalidad",
            ],
        ],
    )

    with pytest.raises(Exception):
        call_command(
            "bootstrap_vat_referentes_centros",
            str(users_file),
            str(centers_file),
            "--default-password=1",
            stdout=StringIO(),
        )
