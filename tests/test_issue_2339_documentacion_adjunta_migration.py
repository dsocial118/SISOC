import importlib
from types import SimpleNamespace

import pytest
from django.apps import apps as global_apps
from django.db import DEFAULT_DB_ALIAS, connection, migrations
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone

from rendicioncuentasmensual.models import DocumentacionAdjunta, RendicionCuentaMensual
from rendicioncuentasmensual.services import RendicionCuentaMensualService


pytestmark = pytest.mark.django_db


_migration = importlib.import_module(
    "rendicioncuentasmensual.migrations.0019_reconciliar_comprobantes_legacy"
)
MIGRATION_BEFORE = [("rendicioncuentasmensual", "0018_stage_permissions")]
MIGRATION_AFTER = [
    ("rendicioncuentasmensual", "0019_reconciliar_comprobantes_legacy"),
]


def _schema_editor_for_default_database():
    return SimpleNamespace(
        connection=SimpleNamespace(alias=DEFAULT_DB_ALIAS),
    )


def _snapshot(documento):
    return {
        "id": documento.id,
        "nombre": documento.nombre,
        "categoria": documento.categoria,
        "estado": documento.estado,
        "observaciones": documento.observaciones,
        "archivo": documento.archivo.name,
        "rendicion_id": documento.rendicion_cuenta_mensual_id,
        "documento_subsanado_id": documento.documento_subsanado_id,
        "deleted_at": documento.deleted_at,
        "deleted_by_id": documento.deleted_by_id,
        "fecha_creacion": documento.fecha_creacion,
        "ultima_modificacion": documento.ultima_modificacion,
    }


def _crear_documento(rendicion, *, nombre, categoria, estado, subsana=None):
    return DocumentacionAdjunta.objects.create(
        nombre=nombre,
        categoria=categoria,
        estado=estado,
        observaciones=f"Observación de {nombre}",
        archivo=f"rendiciones/{nombre}",
        rendicion_cuenta_mensual=rendicion,
        documento_subsanado=subsana,
    )


def test_migracion_reconcilia_legacy_activo_y_baja_logica_sin_perder_datos():
    rendicion = RendicionCuentaMensual.objects.create(mes=8, anio=2026)
    presentado = _crear_documento(
        rendicion,
        nombre="presentado.pdf",
        categoria=_migration.LEGACY_CATEGORY,
        estado=DocumentacionAdjunta.ESTADO_PRESENTADO,
    )
    subsanar = _crear_documento(
        rendicion,
        nombre="subsanar.pdf",
        categoria=_migration.LEGACY_CATEGORY,
        estado=DocumentacionAdjunta.ESTADO_SUBSANAR,
        subsana=presentado,
    )
    validado_baja = _crear_documento(
        rendicion,
        nombre="validado-baja.pdf",
        categoria=_migration.LEGACY_CATEGORY,
        estado=DocumentacionAdjunta.ESTADO_VALIDADO,
    )
    deleted_at = timezone.now()
    DocumentacionAdjunta.all_objects.filter(pk=validado_baja.pk).update(
        deleted_at=deleted_at
    )

    alimentario_pwa = _crear_documento(
        rendicion,
        nombre="alimentario-pwa.pdf",
        categoria=_migration.ALIMENTARIO_CATEGORY,
        estado=DocumentacionAdjunta.ESTADO_VALIDADO,
    )
    siph_pwa = _crear_documento(
        rendicion,
        nombre="siph-pwa.pdf",
        categoria="comprobantes_siph",
        estado=DocumentacionAdjunta.ESTADO_PRESENTADO,
    )

    legacy_ids = [presentado.id, subsanar.id, validado_baja.id]
    snapshots_legacy = {
        documento.pk: _snapshot(documento)
        for documento in DocumentacionAdjunta.all_objects.filter(pk__in=legacy_ids)
    }
    snapshots_pwa = {
        documento.pk: _snapshot(documento)
        for documento in DocumentacionAdjunta.all_objects.filter(
            pk__in=[alimentario_pwa.pk, siph_pwa.pk]
        )
    }

    _migration.reconciliar_comprobantes_legacy(
        global_apps,
        _schema_editor_for_default_database(),
    )

    assert (
        DocumentacionAdjunta.all_objects.filter(
            categoria=_migration.LEGACY_CATEGORY
        ).count()
        == 0
    )
    for documento_id, before in snapshots_legacy.items():
        after = _snapshot(DocumentacionAdjunta.all_objects.get(pk=documento_id))
        assert after == {
            **before,
            "categoria": _migration.ALIMENTARIO_CATEGORY,
        }
    for documento_id, before in snapshots_pwa.items():
        after = _snapshot(DocumentacionAdjunta.all_objects.get(pk=documento_id))
        assert after == before

    detalle_por_categoria = {
        categoria["codigo"]: categoria
        for categoria in RendicionCuentaMensualService.obtener_documentacion_para_detalle(
            rendicion
        )
    }
    archivos_alimentario = {
        archivo.pk
        for archivo in detalle_por_categoria[_migration.ALIMENTARIO_CATEGORY][
            "archivos"
        ]
    }
    archivos_siph = {
        archivo.pk for archivo in detalle_por_categoria["comprobantes_siph"]["archivos"]
    }
    assert {subsanar.pk, alimentario_pwa.pk} <= archivos_alimentario
    assert archivos_siph == {siph_pwa.pk}

    _migration.reconciliar_comprobantes_legacy(
        global_apps,
        _schema_editor_for_default_database(),
    )
    assert (
        DocumentacionAdjunta.all_objects.filter(
            categoria=_migration.LEGACY_CATEGORY
        ).count()
        == 0
    )


def test_migracion_declara_reversa_noop_para_no_mezclar_origenes():
    reverse_code = _migration.Migration.operations[0].reverse_code

    assert reverse_code is migrations.RunPython.noop


@pytest.mark.django_db(transaction=True)
@pytest.mark.mysql_compat
def test_migracion_ejecuta_con_modelo_historico_e_incluye_bajas_logicas():
    if connection.vendor != "mysql":
        pytest.skip(
            "MigrationExecutor requiere el historial de migraciones de MySQL; "
            "la suite SQLite lo desactiva."
        )

    test_failed = False
    try:
        executor = MigrationExecutor(connection)
        executor.migrate(MIGRATION_BEFORE)
        apps_before = executor.loader.project_state(MIGRATION_BEFORE).apps
        rendicion_historica_model = apps_before.get_model(
            "rendicioncuentasmensual", "RendicionCuentaMensual"
        )
        documento_historico_model = apps_before.get_model(
            "rendicioncuentasmensual", "DocumentacionAdjunta"
        )
        rendicion = rendicion_historica_model.objects.create(mes=8, anio=2026)
        activo = documento_historico_model.objects.create(
            nombre="activo.pdf",
            categoria=_migration.LEGACY_CATEGORY,
            estado="presentado",
            archivo="rendiciones/activo.pdf",
            rendicion_cuenta_mensual=rendicion,
        )
        baja_logica = documento_historico_model.objects.create(
            nombre="baja-logica.pdf",
            categoria=_migration.LEGACY_CATEGORY,
            estado="validado",
            archivo="rendiciones/baja-logica.pdf",
            rendicion_cuenta_mensual=rendicion,
        )
        deleted_at = timezone.now()
        documento_historico_model.all_objects.filter(pk=baja_logica.pk).update(
            deleted_at=deleted_at
        )

        executor = MigrationExecutor(connection)
        executor.migrate(MIGRATION_AFTER)
        apps_after = executor.loader.project_state(MIGRATION_AFTER).apps
        documento_reconciliado_model = apps_after.get_model(
            "rendicioncuentasmensual", "DocumentacionAdjunta"
        )

        activo_despues = documento_reconciliado_model.all_objects.get(pk=activo.pk)
        baja_logica_despues = documento_reconciliado_model.all_objects.get(
            pk=baja_logica.pk
        )
        assert activo_despues.categoria == _migration.ALIMENTARIO_CATEGORY
        assert activo_despues.archivo == "rendiciones/activo.pdf"
        assert activo_despues.estado == "presentado"
        assert baja_logica_despues.categoria == _migration.ALIMENTARIO_CATEGORY
        assert baja_logica_despues.archivo == "rendiciones/baja-logica.pdf"
        assert baja_logica_despues.estado == "validado"
        assert baja_logica_despues.deleted_at == deleted_at
    except Exception:
        test_failed = True
        raise
    finally:
        try:
            MigrationExecutor(connection).migrate(MIGRATION_AFTER)
        except Exception:
            if not test_failed:
                raise
