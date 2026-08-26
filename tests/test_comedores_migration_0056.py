"""Regression coverage for the PWA migration history reconciliation."""

import importlib
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import patch

from django.db import migrations


MIGRATION = importlib.import_module(
    "comedores.migrations.0056_imagencomedor_client_uuid_imagencomedor_relevamiento_and_more"
)


class _Apps:
    def __init__(self, model):
        self.model = model

    def get_model(self, app_label, model_name):
        return self.model


class _Introspection:
    def __init__(self, *, columns=(), constraints=()):
        self.columns = columns
        self.constraints = constraints

    def get_table_description(self, cursor, table_name):
        return [SimpleNamespace(name=column) for column in self.columns]

    def get_constraints(self, cursor, table_name):
        return {constraint: {} for constraint in self.constraints}


def _schema_editor(*, columns=(), constraints=()):
    return SimpleNamespace(
        connection=SimpleNamespace(
            alias="default",
            cursor=lambda: nullcontext(),
            introspection=_Introspection(columns=columns, constraints=constraints),
        )
    )


def _state(*, column):
    model = SimpleNamespace(
        _meta=SimpleNamespace(
            db_table="comedores_imagencomedor",
            get_field=lambda name: SimpleNamespace(column=column),
        )
    )
    return SimpleNamespace(apps=_Apps(model))


def test_0056_does_not_readd_existing_client_uuid_column():
    operation = MIGRATION.Migration.operations[0]
    operation.allow_migrate_model = lambda *args: True

    with patch.object(migrations.AddField, "database_forwards") as add_field:
        operation.database_forwards(
            "comedores",
            _schema_editor(columns=("client_uuid",)),
            _state(column="client_uuid"),
            _state(column="client_uuid"),
        )

    add_field.assert_not_called()


def test_0056_adds_client_uuid_column_when_missing():
    operation = MIGRATION.Migration.operations[0]
    operation.allow_migrate_model = lambda *args: True

    with patch.object(migrations.AddField, "database_forwards") as add_field:
        operation.database_forwards(
            "comedores",
            _schema_editor(),
            _state(column="client_uuid"),
            _state(column="client_uuid"),
        )

    add_field.assert_called_once()


def test_0056_does_not_readd_existing_client_uuid_constraint():
    operation = MIGRATION.Migration.operations[2]
    operation.allow_migrate_model = lambda *args: True

    with patch.object(migrations.AddConstraint, "database_forwards") as add_constraint:
        operation.database_forwards(
            "comedores",
            _schema_editor(
                constraints=("uniq_imagencomedor_comedor_client_uuid",),
            ),
            _state(column="client_uuid"),
            _state(column="client_uuid"),
        )

    add_constraint.assert_not_called()


def test_0056_adds_client_uuid_constraint_when_missing():
    operation = MIGRATION.Migration.operations[2]
    operation.allow_migrate_model = lambda *args: True

    with patch.object(migrations.AddConstraint, "database_forwards") as add_constraint:
        operation.database_forwards(
            "comedores",
            _schema_editor(),
            _state(column="client_uuid"),
            _state(column="client_uuid"),
        )

    add_constraint.assert_called_once()
