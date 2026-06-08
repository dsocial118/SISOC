"""Tests unitarios para migraciones de audittrail."""

import importlib

import pytest


@pytest.mark.skip(
    reason="Migración 0002 absorbida por el squash 0001_squashed_0003; test obsoleto"
)
def test_auditlog_performance_indexes_migration_is_non_atomic():
    """La migración de índices manuales debe ejecutarse fuera de transacción."""
    migration_module = importlib.import_module(
        "audittrail.migrations.0002_auditlog_performance_indexes"
    )

    assert migration_module.Migration.atomic is False
