"""Tests for test import flow."""

from io import BytesIO
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from openpyxl import Workbook

from comedores.models import (
    Comedor,
    EstadoActividad,
    EstadoDetalle,
    EstadoProceso,
    Programas,
)
from comedores.services.estado_manager import registrar_cambio_estado
from expedientespagos.models import ExpedientePago
from importarexpediente.models import (
    ArchivosImportados,
    ErroresImportacion,
    ExitoImportacion,
    RegistroImportado,
)


User = get_user_model()
ACTIVO = "Activo"
INACTIVO = "Inactivo"
EN_EJECUCION = "En ejecuci\u00f3n"
EN_PROCESO_RENOVACION = "En proceso - Renovaci\u00f3n"
BAJA = "Baja"
EN_PLAZO_RENOVACION = "En plazo de renovaci\u00f3n"
NO_RENOVACION_COMEDOR = "No renovaci\u00f3n (Comedor)"

# Enable DB access for all tests in this module
pytestmark = pytest.mark.django_db


@pytest.fixture
def user(db):
    return User.objects.create_user(username="tester", password="pass1234")


@pytest.fixture
def client_logged(client, user):
    client.login(username="tester", password="pass1234")
    return client


@pytest.fixture
def tmp_media(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
    return settings.MEDIA_ROOT


def _make_csv(comedor_pk, mes_convenio=None, expediente_pago="EX-2025-BBB"):
    # Sample aligned to new HEADER_MAP (semicolon-delimited)
    headers = (
        "ID;COMEDOR;ORGANIZACIÓN;EXPEDIENTE del CONVENIO;Expediente de Pago;"
        "Prestaciones Mensuales Desayuno;Prestaciones Mensuales Almuerzo;"
        "Prestaciones Mensuales Merienda;Prestaciones Mensuales Cena;"
        "Monto Mensuales Desayuno;Monto Mensuales Almuerzo;"
        "Monto Mensuales Merienda;Monto Mensuales Cena;TOTAL;Mes de Pago;Año"
    )
    if mes_convenio is not None:
        headers += ";Mes de Convenio"
    headers += "\n"
    row = (
        f"{comedor_pk};Comedor Prueba;Org X;EX-2024-AAA;{expediente_pago};150;0;0;750;"
        "$ 57.450,00;$ 0,00;$ 0,00;$ 572.250,00;$ 629.700,00;septiembre;2025"
    )
    if mes_convenio is not None:
        row += f";{mes_convenio}"
    row += "\n"
    return headers + row


def _make_xlsx(comedor_pk, mes_convenio=4):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "4quefuncionan"
    sheet.append(
        [
            "ID",
            "COMEDOR",
            "ORGANIZACION",
            "EXPEDIENTE del CONVENIO",
            "Expediente de Pago",
            "Prestaciones Mensuales Desayuno",
            "Prestaciones Mensuales Almuerzo",
            "Prestaciones Mensuales Merienda",
            "Prestaciones Mensuales Cena",
            "Monto Mensuales Desayuno",
            "Monto Mensuales Almuerzo",
            "Monto Mensuales Merienda",
            "Monto Mensuales Cena",
            "TOTAL",
            "Mes de Pago",
            "A\u00f1o",
            "Provincia",
            "PARTIDO / DEPARTAMENTO",
            "Municipio",
            "LOCALIDAD",
            "BARRIO",
            "CALLE",
            "ALTURA",
            "ENTRE CALLE 1",
            "ENTRE CALLE 2",
            "MZ",
            "LOTE",
            "Mes de Convenio",
        ]
    )
    sheet.append(
        [
            comedor_pk,
            "Comedor Prueba",
            "Org X",
            "EX-2024-AAA",
            "EX-2025-XLSX",
            150,
            0,
            0,
            750,
            57450,
            0,
            0,
            572250,
            629700,
            "septiembre",
            "2025",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            mes_convenio,
        ]
    )
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def _estado_catalog():
    activo, _ = EstadoActividad.objects.get_or_create(estado=ACTIVO)
    inactivo, _ = EstadoActividad.objects.get_or_create(estado=INACTIVO)
    en_ejecucion, _ = EstadoProceso.objects.get_or_create(
        estado=EN_EJECUCION, estado_actividad=activo
    )
    en_proceso_renovacion, _ = EstadoProceso.objects.get_or_create(
        estado=EN_PROCESO_RENOVACION, estado_actividad=activo
    )
    baja, _ = EstadoProceso.objects.get_or_create(
        estado=BAJA, estado_actividad=inactivo
    )
    en_plazo, _ = EstadoDetalle.objects.get_or_create(
        estado=EN_PLAZO_RENOVACION, estado_proceso=en_ejecucion
    )
    no_renovacion, _ = EstadoDetalle.objects.get_or_create(
        estado=NO_RENOVACION_COMEDOR, estado_proceso=baja
    )
    return {
        "activo": activo,
        "inactivo": inactivo,
        "en_ejecucion": en_ejecucion,
        "en_proceso_renovacion": en_proceso_renovacion,
        "baja": baja,
        "en_plazo": en_plazo,
        "no_renovacion": no_renovacion,
    }


def _programa_alimentar():
    programa, _ = Programas.objects.get_or_create(
        id=2, defaults={"nombre": "Alimentar comunidad"}
    )
    return programa


def _programa_no_alimentar():
    programa, _ = Programas.objects.get_or_create(
        id=3, defaults={"nombre": "Otro programa"}
    )
    return programa


def _set_estado(comedor, actividad, proceso, detalle=None):
    registrar_cambio_estado(
        comedor=comedor,
        actividad=actividad,
        proceso=proceso,
        detalle=detalle,
    )


def _estado_tuple(comedor):
    comedor.refresh_from_db()
    estado_general = comedor.ultimo_estado.estado_general
    detalle = estado_general.estado_detalle
    return (
        estado_general.estado_actividad.estado,
        estado_general.estado_proceso.estado,
        detalle.estado if detalle else None,
    )


def _upload_csv_and_import(client_logged, comedor, mes_convenio, expediente_pago):
    uploaded = SimpleUploadedFile(
        f"{expediente_pago}.csv",
        _make_csv(comedor.pk, mes_convenio, expediente_pago).encode("utf-8"),
        content_type="text/csv",
    )
    client_logged.post(
        reverse("upload"),
        {"file": uploaded, "delimiter": ";", "has_header": True},
    )
    batch = ArchivosImportados.objects.latest("id")
    client_logged.post(reverse("importar_datos", kwargs={"id_archivo": batch.id}))
    return batch


def test_upload_validation_success_creates_batch_and_logs_success(
    client_logged, tmp_media, db
):
    comedor = Comedor.objects.create(nombre="Comedor Uno")

    csv_bytes = _make_csv(comedor.pk).encode("utf-8")
    uploaded = SimpleUploadedFile("expedientes.csv", csv_bytes, content_type="text/csv")

    url = reverse("upload")
    resp = client_logged.post(
        url,
        {
            "file": uploaded,
            "delimiter": ";",
            "has_header": True,
        },
        follow=True,
    )

    assert resp.status_code in (302, 200)

    # One master record is created
    assert ArchivosImportados.objects.count() == 1
    batch = ArchivosImportados.objects.first()

    # Success logged, no errors
    assert ExitoImportacion.objects.filter(archivo_importado=batch).count() == 1
    assert ErroresImportacion.objects.filter(archivo_importado=batch).count() == 0
    # Captured expediente de pago number in batch
    assert batch.numero_expediente_pago == "EX-2025-BBB"

    # Counters persisted in master
    batch.refresh_from_db()
    assert batch.count_exitos == 1
    assert batch.count_errores == 0


def test_upload_validation_xlsx_creates_batch_and_logs_mes_convenio_success(
    client_logged, tmp_media, db
):
    comedor = Comedor.objects.create(nombre="Comedor XLSX")
    uploaded = SimpleUploadedFile(
        "expedientes.xlsx",
        _make_xlsx(comedor.pk, mes_convenio=4),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    resp = client_logged.post(
        reverse("upload"),
        {
            "file": uploaded,
            "delimiter": ";",
            "has_header": True,
        },
    )

    assert resp.status_code in (302, 200)
    batch = ArchivosImportados.objects.latest("id")
    assert batch.numero_expediente_pago == "EX-2025-XLSX"
    assert batch.count_exitos == 1
    assert batch.count_errores == 0
    assert ExitoImportacion.objects.filter(archivo_importado=batch).count() == 1


def test_upload_validation_rejects_invalid_mes_convenio(client_logged, tmp_media, db):
    comedor = Comedor.objects.create(nombre="Comedor Mes Invalido")
    uploaded = SimpleUploadedFile(
        "expedientes.csv",
        _make_csv(comedor.pk, mes_convenio=7).encode("utf-8"),
        content_type="text/csv",
    )

    resp = client_logged.post(
        reverse("upload"),
        {"file": uploaded, "delimiter": ";", "has_header": True},
    )

    assert resp.status_code in (302, 200)
    batch = ArchivosImportados.objects.latest("id")
    assert batch.count_exitos == 0
    assert batch.count_errores == 1
    assert ErroresImportacion.objects.filter(
        archivo_importado=batch, mensaje__icontains="Mes de convenio"
    ).exists()


def test_upload_validation_empty_csv_logs_error_and_counters(
    client_logged, tmp_media, db
):
    uploaded = SimpleUploadedFile("vacio.csv", b"", content_type="text/csv")
    url = reverse("upload")
    resp = client_logged.post(
        url,
        {
            "file": uploaded,
            "delimiter": ",",
            "has_header": True,
        },
    )
    assert resp.status_code in (302, 200)
    # If form was invalid, there will be no batch
    if ArchivosImportados.objects.count() == 0:
        return

    # Otherwise, a batch should exist with one error and zero successes
    batch = ArchivosImportados.objects.order_by("-id").first()
    assert batch is not None
    batch.refresh_from_db()
    assert batch.count_exitos == 0
    assert batch.count_errores == 1
    assert ErroresImportacion.objects.filter(archivo_importado=batch, fila=0).exists()


def test_import_persists_expedientepago_and_marks_completed(
    client_logged, tmp_media, db
):
    comedor = Comedor.objects.create(nombre="Comedor Dos")

    # Step 1: upload to create batch and success log
    csv_bytes = _make_csv(comedor.pk).encode("utf-8")
    uploaded = SimpleUploadedFile("expedientes.csv", csv_bytes, content_type="text/csv")
    upload_url = reverse("upload")
    client_logged.post(
        upload_url,
        {
            "file": uploaded,
            "delimiter": ";",
            "has_header": True,
        },
    )

    batch = ArchivosImportados.objects.latest("id")

    # Step 2: import
    import_url = reverse("importar_datos", kwargs={"id_archivo": batch.id})
    resp = client_logged.post(import_url)
    assert resp.status_code in (302, 200)

    # One ExpedientePago created
    assert ExpedientePago.objects.count() == 1
    exp = ExpedientePago.objects.first()
    assert exp is not None
    # Check key fields parsed according to new headers
    assert exp.comedor_id == comedor.id
    assert exp.expediente_pago == "EX-2025-BBB"
    assert exp.expediente_convenio == "EX-2024-AAA"
    assert exp.prestaciones_mensuales_desayuno == 150
    assert exp.prestaciones_mensuales_cena == 750
    assert exp.monto_mensual_desayuno == Decimal("57450")
    assert exp.monto_mensual_cena == Decimal("572250")
    assert exp.total == Decimal("629700")
    assert str(exp.mes_pago).lower() == "septiembre"
    assert str(exp.ano) == "2025"

    # RegistroImportado linking success entry with expediente
    assert RegistroImportado.objects.count() == 1

    # Batch marked completed
    batch.refresh_from_db()
    assert batch.importacion_completada is True


def test_import_xlsx_persists_mes_convenio_and_updates_present_state(
    client_logged, tmp_media, db
):
    estados = _estado_catalog()
    programa = _programa_alimentar()
    comedor = Comedor.objects.create(nombre="Comedor Mes 4", programa=programa)
    uploaded = SimpleUploadedFile(
        "expedientes.xlsx",
        _make_xlsx(comedor.pk, mes_convenio=4),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    client_logged.post(
        reverse("upload"),
        {"file": uploaded, "delimiter": ";", "has_header": True},
    )
    batch = ArchivosImportados.objects.latest("id")

    resp = client_logged.post(
        reverse("importar_datos", kwargs={"id_archivo": batch.id})
    )

    assert resp.status_code in (302, 200)
    batch.refresh_from_db()
    exp = ExpedientePago.objects.get()
    assert exp.mes_convenio == 4
    assert batch.importacion_completada is True
    assert _estado_tuple(comedor) == (
        ACTIVO,
        EN_EJECUCION,
        estados["en_plazo"].estado,
    )


def test_import_detail_displays_mes_convenio(client_logged, tmp_media, db):
    programa = _programa_alimentar()
    comedor = Comedor.objects.create(nombre="Comedor Detail", programa=programa)
    _estado_catalog()
    batch = _upload_csv_and_import(client_logged, comedor, 1, "EX-2025-DETAIL")
    exp = ExpedientePago.objects.get(
        registros_importados__exito_importacion__archivo_importado=batch
    )

    resp = client_logged.get(reverse("expedientespagos_detail", kwargs={"pk": exp.pk}))

    assert resp.status_code == 200
    assert b"Mes de Convenio" in resp.content
    assert b"1" in resp.content


def test_import_updates_present_mes_1_to_active_execution(client_logged, tmp_media, db):
    estados = _estado_catalog()
    programa = _programa_alimentar()
    comedor = Comedor.objects.create(nombre="Comedor Mes 1", programa=programa)

    _upload_csv_and_import(client_logged, comedor, 1, "EX-2025-MES1")

    assert _estado_tuple(comedor) == (ACTIVO, EN_EJECUCION, None)
    assert comedor.historial_estados.count() == 1
    assert estados["en_ejecucion"].estado == EN_EJECUCION


def test_import_estado_update_does_not_sync_comedor_payload(
    client_logged, tmp_media, db, mocker
):
    _estado_catalog()
    programa = _programa_alimentar()
    comedor = Comedor.objects.create(
        nombre="Comedor Estado Sin Sync", programa=programa
    )
    build_comedor_payload = mocker.patch("comedores.signals.build_comedor_payload")

    _upload_csv_and_import(client_logged, comedor, 1, "EX-2025-ESTADO-SIN-SYNC")

    build_comedor_payload.assert_not_called()


def test_import_updates_present_mes_6_to_active_execution_en_plazo(
    client_logged, tmp_media, db
):
    estados = _estado_catalog()
    programa = _programa_alimentar()
    comedor = Comedor.objects.create(nombre="Comedor Mes 6", programa=programa)

    _upload_csv_and_import(client_logged, comedor, 6, "EX-2025-MES6")

    assert _estado_tuple(comedor) == (
        ACTIVO,
        EN_EJECUCION,
        estados["en_plazo"].estado,
    )
    assert comedor.historial_estados.count() == 1


def test_import_does_not_update_estado_for_other_program(client_logged, tmp_media, db):
    estados = _estado_catalog()
    programa = _programa_no_alimentar()
    comedor = Comedor.objects.create(nombre="Comedor Otro Programa", programa=programa)
    _set_estado(comedor, estados["activo"], estados["en_ejecucion"])

    _upload_csv_and_import(client_logged, comedor, 6, "EX-2025-OTRO")

    assert _estado_tuple(comedor) == (ACTIVO, EN_EJECUCION, None)
    assert comedor.historial_estados.count() == 1


def test_import_updates_absent_active_program2_by_consecutive_batches(
    client_logged, tmp_media, db
):
    estados = _estado_catalog()
    programa = _programa_alimentar()
    present = Comedor.objects.create(nombre="Comedor Presente", programa=programa)
    absent = Comedor.objects.create(nombre="Comedor Ausente", programa=programa)
    _set_estado(absent, estados["activo"], estados["en_ejecucion"])

    _upload_csv_and_import(client_logged, present, 1, "EX-2025-AUS-1")
    assert _estado_tuple(absent) == (ACTIVO, EN_PROCESO_RENOVACION, None)

    _upload_csv_and_import(client_logged, present, 1, "EX-2025-AUS-2")
    assert _estado_tuple(absent) == (ACTIVO, EN_PROCESO_RENOVACION, None)

    _upload_csv_and_import(client_logged, present, 1, "EX-2025-AUS-3")
    assert _estado_tuple(absent) == (INACTIVO, BAJA, NO_RENOVACION_COMEDOR)


def test_import_keeps_inactive_absent_program2_as_no_renovacion(
    client_logged, tmp_media, db
):
    estados = _estado_catalog()
    programa = _programa_alimentar()
    present = Comedor.objects.create(
        nombre="Comedor Presente Inactivo", programa=programa
    )
    inactive_absent = Comedor.objects.create(
        nombre="Comedor Inactivo Ausente", programa=programa
    )
    _set_estado(
        inactive_absent,
        estados["inactivo"],
        estados["baja"],
        estados["no_renovacion"],
    )

    _upload_csv_and_import(client_logged, present, 1, "EX-2025-INACTIVO")

    assert _estado_tuple(inactive_absent) == (
        INACTIVO,
        BAJA,
        NO_RENOVACION_COMEDOR,
    )
    assert inactive_absent.historial_estados.count() == 1


def test_import_is_idempotent_when_completed(client_logged, tmp_media, db):
    _estado_catalog()
    programa = _programa_alimentar()
    comedor = Comedor.objects.create(nombre="Comedor Tres", programa=programa)

    csv_bytes = _make_csv(comedor.pk, mes_convenio=1).encode("utf-8")
    uploaded = SimpleUploadedFile("expedientes.csv", csv_bytes, content_type="text/csv")
    client_logged.post(
        reverse("upload"),
        {"file": uploaded, "delimiter": ";", "has_header": True},
    )
    batch = ArchivosImportados.objects.latest("id")

    # First import
    client_logged.post(reverse("importar_datos", kwargs={"id_archivo": batch.id}))
    assert ExpedientePago.objects.count() == 1
    assert comedor.historial_estados.count() == 1

    # Second import should not create more
    resp = client_logged.post(
        reverse("importar_datos", kwargs={"id_archivo": batch.id}), follow=True
    )
    assert resp.status_code == 200
    assert ExpedientePago.objects.count() == 1
    assert comedor.historial_estados.count() == 1


def test_delete_resets_flag_and_removes_records(client_logged, tmp_media, db):
    comedor = Comedor.objects.create(nombre="Comedor Cuatro")

    csv_bytes = _make_csv(comedor.pk).encode("utf-8")
    uploaded = SimpleUploadedFile("expedientes.csv", csv_bytes, content_type="text/csv")
    client_logged.post(
        reverse("upload"),
        {"file": uploaded, "delimiter": ",", "has_header": True},
    )
    batch = ArchivosImportados.objects.latest("id")

    # Import to create records
    client_logged.post(reverse("importar_datos", kwargs={"id_archivo": batch.id}))
    assert ExpedientePago.objects.count() == 1
    batch.refresh_from_db()
    assert batch.importacion_completada is True

    # Delete imported data
    resp = client_logged.post(
        reverse("borrar_datos_importados", kwargs={"id_archivo": batch.id})
    )
    assert resp.status_code in (302, 200)

    # All imported records removed and flag reset
    assert ExpedientePago.objects.count() == 0
    assert RegistroImportado.objects.count() == 0
    batch.refresh_from_db()
    assert batch.importacion_completada is False
