from io import StringIO

import pytest
from django.contrib.auth.models import Group, User
from django.core.management import call_command
from openpyxl import Workbook

from VAT.models import Centro, InstitucionContacto, InstitucionIdentificadorHist
from VAT.models import InstitucionUbicacion
from core.models import Localidad, Municipio, Provincia


pytestmark = pytest.mark.django_db


def _build_excel_file(tmp_path, rows):
    workbook = Workbook()
    worksheet = workbook.active
    for row in rows:
        worksheet.append(row)
    file_path = tmp_path / "centros_vat.xlsx"
    workbook.save(file_path)
    return file_path


def test_import_vat_centros_excel_creates_centro_relations_and_contact(tmp_path):
    provincia = Provincia.objects.create(id=2, nombre="Buenos Aires")
    municipio = Municipio.objects.create(
        id=92, nombre="General Pueyrredon", provincia=provincia
    )
    localidad = Localidad.objects.create(
        id=3085, nombre="Mar del Plata", municipio=municipio
    )
    group, _ = Group.objects.get_or_create(name="CFP")
    referente = User.objects.create_user(username="cfp-ref", password="1")
    referente.groups.add(group)

    file_path = _build_excel_file(
        tmp_path,
        [
            [
                "nombre",
                "codigo",
                "provincia_id",
                "municipio_id",
                "localidad_id",
                "domicilio_actividad",
                "telefono",
                "correo",
                "referente_id",
                "tipo_gestion",
                "clase_institucion",
                "situacion",
                "autoridad_dni",
                "contacto_nombre",
                "contacto_rol_area",
                "contacto_telefono",
                "contacto_email",
                "contacto_es_principal",
            ],
            [
                "Escuela Municipal De Formación Profesional Nº 1",
                "616126000",
                "2",
                "92",
                "3085",
                "SAN MARTIN 5420",
                "2234727869",
                "efpmun1@yahoo.com.ar",
                str(referente.pk),
                "Estatal",
                "Formación Profesional",
                "Institución de ETP",
                "30111222",
                "Maria Gomez",
                "Administracion",
                "2234000000",
                "maria@vat.test",
                "1",
            ],
        ],
    )

    call_command("import_vat_centros_excel", str(file_path), stdout=StringIO())

    centro = Centro.objects.get(codigo="616126000")
    contacto = InstitucionContacto.objects.get(centro=centro)

    assert centro.nombre == "Escuela Municipal De Formación Profesional Nº 1"
    assert centro.referente_id == referente.pk
    assert centro.tipo_gestion == "Estatal"
    assert centro.nombre_referente == "Maria Gomez"
    assert contacto.es_principal is True
    assert contacto.documento == "30111222"
    assert InstitucionUbicacion.objects.filter(
        centro=centro,
        localidad=localidad,
        rol_ubicacion="sede_principal",
        es_principal=True,
    ).exists()
    assert InstitucionIdentificadorHist.objects.filter(
        centro=centro,
        tipo_identificador="cue",
        valor_identificador="616126000",
    ).exists()


def test_import_vat_centros_excel_generates_fantasy_email_and_normalizes_gestion(
    tmp_path,
):
    provincia = Provincia.objects.create(id=23, nombre="Tucuman")
    municipio = Municipio.objects.create(id=800, nombre="Capital", provincia=provincia)

    file_path = _build_excel_file(
        tmp_path,
        [
            [
                "nombre",
                "codigo",
                "provincia_id",
                "municipio_id",
                "domicilio_actividad",
                "tipo_gestion",
                "clase_institucion",
                "situacion",
            ],
            [
                "Centro C. E. J. A. Adultos N° 3",
                "900001800",
                "23",
                "800",
                "SARGENTO CABRAL 576",
                "Privado",
                "Formación Profesional",
                "Institución de Otro Nivel y/o Modalidad",
            ],
        ],
    )

    call_command("import_vat_centros_excel", str(file_path), stdout=StringIO())

    centro = Centro.objects.get(codigo="900001800")

    assert centro.correo == "centro1800@vat.local"
    assert centro.tipo_gestion == "Privada"


def test_import_vat_centros_excel_dry_run_does_not_persist(tmp_path):
    file_path = _build_excel_file(
        tmp_path,
        [
            ["nombre", "codigo", "tipo_gestion", "clase_institucion", "situacion"],
            [
                "Centro De Formación Laboral Nº 1",
                "615050000",
                "Estatal",
                "Formación Profesional",
                "Institución de ETP",
            ],
        ],
    )

    out = StringIO()
    call_command(
        "import_vat_centros_excel",
        str(file_path),
        "--dry-run",
        stdout=out,
    )

    assert not Centro.objects.filter(codigo="615050000").exists()
    assert "Simulación finalizada" in out.getvalue()


def test_import_vat_centros_excel_pads_codigo_with_leading_zeroes(tmp_path):
    file_path = _build_excel_file(
        tmp_path,
        [
            ["nombre", "codigo", "tipo_gestion", "clase_institucion", "situacion"],
            [
                "Centro De Formación Laboral Nº 1",
                "12345",
                "Estatal",
                "Formación Profesional",
                "Institución de ETP",
            ],
        ],
    )

    call_command("import_vat_centros_excel", str(file_path), stdout=StringIO())

    centro = Centro.objects.get(codigo="000012345")

    assert centro.codigo == "000012345"
    assert centro.correo == "centro2345@vat.local"


def test_import_vat_centros_excel_uses_localidad_as_source_of_truth(tmp_path):
    provincia_correcta = Provincia.objects.create(id=2, nombre="Buenos Aires")
    municipio_correcto = Municipio.objects.create(
        id=92, nombre="General Pueyrredon", provincia=provincia_correcta
    )
    localidad = Localidad.objects.create(
        id=3085, nombre="Mar del Plata", municipio=municipio_correcto
    )

    file_path = _build_excel_file(
        tmp_path,
        [
            [
                "nombre",
                "codigo",
                "provincia_id",
                "municipio_id",
                "localidad_id",
                "tipo_gestion",
                "clase_institucion",
                "situacion",
            ],
            [
                "Centro C. E. J. A. Adultos N° 3",
                "900001800",
                "2",
                "92",
                "3085",
                "Estatal",
                "Formación Profesional",
                "Institución de Otro Nivel y/o Modalidad",
            ],
        ],
    )

    call_command("import_vat_centros_excel", str(file_path), stdout=StringIO())

    centro = Centro.objects.get(codigo="900001800")

    assert centro.localidad_id == localidad.id
    assert centro.municipio_id == municipio_correcto.id
    assert centro.provincia_id == provincia_correcta.id


def test_import_vat_centros_excel_keeps_only_provincia_on_geo_mismatch(tmp_path):
    provincia = Provincia.objects.create(id=2, nombre="Buenos Aires")
    provincia_otra = Provincia.objects.create(id=3, nombre="Cordoba")
    municipio_correcto = Municipio.objects.create(
        id=92, nombre="General Pueyrredon", provincia=provincia
    )
    Municipio.objects.create(id=500, nombre="Capital", provincia=provincia_otra)
    Localidad.objects.create(
        id=3085, nombre="Mar del Plata", municipio=municipio_correcto
    )

    file_path = _build_excel_file(
        tmp_path,
        [
            [
                "nombre",
                "codigo",
                "provincia_id",
                "municipio_id",
                "localidad_id",
                "tipo_gestion",
                "clase_institucion",
                "situacion",
            ],
            [
                "Centro C. E. J. A. Adultos N° 3",
                "900001800",
                "2",
                "500",
                "3085",
                "Estatal",
                "Formación Profesional",
                "Institución de Otro Nivel y/o Modalidad",
            ],
        ],
    )

    call_command("import_vat_centros_excel", str(file_path), stdout=StringIO())

    centro = Centro.objects.get(codigo="900001800")

    assert centro.provincia_id == provincia.id
    assert centro.municipio_id is None
    assert centro.localidad_id is None
