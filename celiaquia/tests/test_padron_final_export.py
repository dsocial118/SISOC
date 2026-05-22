"""Tests de exportacion de nomina aprobada Celiaquia."""

from io import BytesIO

import pytest
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.urls import reverse
from openpyxl import Workbook, load_workbook

from celiaquia.models import (
    EstadoExpediente,
    EstadoLegajo,
    Expediente,
    ExpedienteCiudadano,
    ResultadoSintys,
    RevisionTecnico,
)
from celiaquia.services.padron_final_service import PadronFinalService
from ciudadanos.models import Ciudadano


NOMINA_HEADERS = [
    "apellido",
    "nombre",
    "documento",
    "fecha_nacimiento",
    "sexo",
    "nacionalidad",
    "municipio",
    "localidad",
    "calle",
    "altura",
    "codigo_postal",
    "telefono",
    "email",
    "APELLIDO_RESPONSABLE",
    "NOMBRE_RESPONSABLE",
    "Cuit_Responsable",
    "FECHA_DE_NACIMIENTO_RESPONSABLE",
    "SEXO_RESPONSABLE",
    "DOMICILIO_RESPONSABLE",
    "LOCALIDAD_RESPONSABLE",
    "CELULAR_RESPONSABLE",
    "CORREO_RESPONSABLE",
]


def _permission(app_label, codename):
    try:
        return Permission.objects.get(
            content_type__app_label=app_label,
            codename=codename,
        )
    except Permission.DoesNotExist:
        content_type = ContentType.objects.get(app_label="auth", model="user")
        return Permission.objects.create(
            content_type=content_type,
            codename=codename,
            name=codename,
        )


def _grant(user, app_label, codename):
    user.user_permissions.add(_permission(app_label, codename))


def _user(username, *, coord=False):
    user = User.objects.create_user(username=username, password="pass")
    _grant(user, "celiaquia", "view_expediente")
    if coord:
        _grant(user, "auth", "role_coordinadorceliaquia")
    return user


def _excel_bytes(rows):
    wb = Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws.append(NOMINA_HEADERS)
    for row in rows:
        ws.append([row.get(header) for header in NOMINA_HEADERS])

    output = BytesIO()
    wb.save(output)
    return output.getvalue()


def _row(documento, apellido, nombre, **extra):
    data = {
        "apellido": apellido,
        "nombre": nombre,
        "documento": documento,
        "fecha_nacimiento": "2000-10-10",
        "sexo": "M",
        "nacionalidad": "ARGENTINA",
        "municipio": "1353",
        "localidad": "8842",
        "calle": "Calle",
        "altura": "1",
        "codigo_postal": "1900",
    }
    data.update(extra)
    return data


def _workbook_rows(content):
    wb = load_workbook(BytesIO(content))
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    return rows[0], rows[1:]


def _expediente_con_excel(
    settings, tmp_path, owner, rows, *, estado="CRUCE_FINALIZADO"
):
    settings.MEDIA_ROOT = tmp_path
    expediente = Expediente.objects.create(
        usuario_provincia=owner,
        estado=EstadoExpediente.objects.create(nombre=estado),
    )
    expediente.excel_masivo.save(
        "nomina_original.xlsx",
        ContentFile(_excel_bytes(rows)),
        save=True,
    )
    return expediente


def _crear_legajo(expediente, documento, *, revision, sintys, rol=None):
    estado_legajo, _ = EstadoLegajo.objects.get_or_create(nombre="VALIDO")
    ciudadano = Ciudadano.objects.create(
        apellido=f"Apellido {documento}",
        nombre=f"Nombre {documento}",
        fecha_nacimiento="2000-01-01",
        documento=int(documento),
    )
    return ExpedienteCiudadano.objects.create(
        expediente=expediente,
        ciudadano=ciudadano,
        estado=estado_legajo,
        revision_tecnico=revision,
        resultado_sintys=sintys,
        rol=rol or ExpedienteCiudadano.ROLE_BENEFICIARIO,
    )


@pytest.mark.django_db
def test_nomina_aprobados_conserva_estructura_original_y_filtra_aprobados(
    settings, tmp_path
):
    owner = _user("prov-servicio")
    rows = [
        _row(
            "20392317989",
            "alzueta",
            "lucas",
            APELLIDO_RESPONSABLE="adulto",
            NOMBRE_RESPONSABLE="responsable",
            Cuit_Responsable="27222222222",
        ),
        _row("20392317990", "no", "match"),
        _row("20392317991", "rechazado", "tecnico"),
        _row("20392317992", "responsable", "puro"),
    ]
    expediente = _expediente_con_excel(settings, tmp_path, owner, rows)

    _crear_legajo(
        expediente,
        "20392317989",
        revision=RevisionTecnico.APROBADO,
        sintys=ResultadoSintys.MATCH,
    )
    _crear_legajo(
        expediente,
        "20392317990",
        revision=RevisionTecnico.APROBADO,
        sintys=ResultadoSintys.NO_MATCH,
    )
    _crear_legajo(
        expediente,
        "20392317991",
        revision=RevisionTecnico.RECHAZADO,
        sintys=ResultadoSintys.MATCH,
    )
    _crear_legajo(
        expediente,
        "20392317992",
        revision=RevisionTecnico.APROBADO,
        sintys=ResultadoSintys.MATCH,
        rol=ExpedienteCiudadano.ROLE_RESPONSABLE,
    )

    header, data_rows = _workbook_rows(
        PadronFinalService.generar_padron_final_excel(expediente)
    )

    assert list(header) == NOMINA_HEADERS
    assert len(data_rows) == 1
    assert data_rows[0][NOMINA_HEADERS.index("documento")] == "20392317989"
    assert data_rows[0][NOMINA_HEADERS.index("APELLIDO_RESPONSABLE")] == "adulto"
    assert data_rows[0][NOMINA_HEADERS.index("Cuit_Responsable")] == "27222222222"


@pytest.mark.django_db
def test_nomina_aprobados_se_recalcula_con_resultado_sintys_actual(settings, tmp_path):
    owner = _user("prov-reproceso")
    rows = [
        _row("20392317001", "primero", "match"),
        _row("20392317002", "segundo", "reprocesado"),
    ]
    expediente = _expediente_con_excel(settings, tmp_path, owner, rows)
    _crear_legajo(
        expediente,
        "20392317001",
        revision=RevisionTecnico.APROBADO,
        sintys=ResultadoSintys.MATCH,
    )
    reprocesado = _crear_legajo(
        expediente,
        "20392317002",
        revision=RevisionTecnico.APROBADO,
        sintys=ResultadoSintys.NO_MATCH,
    )

    _, data_rows = _workbook_rows(
        PadronFinalService.generar_padron_final_excel(expediente)
    )
    assert [row[NOMINA_HEADERS.index("documento")] for row in data_rows] == [
        "20392317001"
    ]

    reprocesado.resultado_sintys = ResultadoSintys.MATCH
    reprocesado.save(update_fields=["resultado_sintys"])

    _, data_rows = _workbook_rows(
        PadronFinalService.generar_padron_final_excel(expediente)
    )
    assert [row[NOMINA_HEADERS.index("documento")] for row in data_rows] == [
        "20392317001",
        "20392317002",
    ]


@pytest.mark.django_db
def test_descarga_nomina_aprobados_no_disponible_antes_de_cruce_finalizado(
    client, settings, tmp_path
):
    owner = _user("prov-antes")
    coord = _user("coord-antes", coord=True)
    expediente = _expediente_con_excel(
        settings,
        tmp_path,
        owner,
        [_row("20392317101", "pendiente", "cruce")],
        estado="ASIGNADO",
    )

    client.force_login(coord)
    response = client.get(
        reverse("expediente_padron_final_export", args=[expediente.pk])
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_descarga_nomina_aprobados_finalizada_devuelve_xlsx(client, settings, tmp_path):
    owner = _user("prov-final")
    coord = _user("coord-final", coord=True)
    expediente = _expediente_con_excel(
        settings,
        tmp_path,
        owner,
        [_row("20392317201", "final", "aprobado")],
    )
    _crear_legajo(
        expediente,
        "20392317201",
        revision=RevisionTecnico.APROBADO,
        sintys=ResultadoSintys.MATCH,
    )

    client.force_login(coord)
    response = client.get(
        reverse("expediente_padron_final_export", args=[expediente.pk])
    )

    assert response.status_code == 200
    assert (
        response["Content-Type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert (
        f"nomina_aprobados_{expediente.pk}.xlsx"
        in response.headers["Content-Disposition"]
    )
    header, data_rows = _workbook_rows(response.content)
    assert list(header) == NOMINA_HEADERS
    assert data_rows[0][NOMINA_HEADERS.index("documento")] == "20392317201"


@pytest.mark.django_db
def test_detalle_muestra_descarga_solo_con_cruce_finalizado(client, settings, tmp_path):
    owner = _user("prov-detalle")
    coord = _user("coord-detalle", coord=True)
    expediente_asignado = _expediente_con_excel(
        settings,
        tmp_path,
        owner,
        [_row("20392317301", "asignado", "sin-cruce")],
        estado="ASIGNADO",
    )
    expediente_finalizado = _expediente_con_excel(
        settings,
        tmp_path,
        owner,
        [_row("20392317302", "finalizado", "con-cruce")],
    )

    client.force_login(coord)
    response_asignado = client.get(
        reverse("expediente_detail", args=[expediente_asignado.pk])
    )
    response_finalizado = client.get(
        reverse("expediente_detail", args=[expediente_finalizado.pk])
    )

    assert response_asignado.status_code == 200
    assert response_finalizado.status_code == 200
    assert (
        reverse("expediente_padron_final_export", args=[expediente_asignado.pk])
        not in response_asignado.content.decode()
    )
    assert "Descargar nómina aprobados" in response_finalizado.content.decode()
