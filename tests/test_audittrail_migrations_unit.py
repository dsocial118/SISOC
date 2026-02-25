"""Tests unitarios para migraciones de audittrail."""

import importlib


def test_auditlog_performance_indexes_migration_is_non_atomic():
    """La migración de índices manuales debe ejecutarse fuera de transacción."""
    migration_module = importlib.import_module(
        "audittrail.migrations.0002_auditlog_performance_indexes"
    )

    assert migration_module.Migration.atomic is False
