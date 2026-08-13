from importlib import import_module

from django.db import migrations, models


migration_0042 = import_module(
    "centrodeinfancia.migrations.0042_alter_nominacentroinfancia_talla"
)
migration_0043 = import_module(
    "centrodeinfancia.migrations.0043_revert_nominacentroinfancia_talla_to_text"
)


def test_0042_no_convierte_las_tallas_legacy():
    """La migración fallida debe poder cruzarse sin transformar datos existentes."""

    (operation,) = migration_0042.Migration.operations
    assert isinstance(operation, migrations.SeparateDatabaseAndState)
    assert operation.database_operations == []
    (state_operation,) = operation.state_operations
    assert isinstance(state_operation, migrations.AlterField)
    assert isinstance(state_operation.field, models.DecimalField)


def test_0043_restaura_la_columna_talla_a_texto():
    assert migration_0043.Migration.dependencies == [
        ("centrodeinfancia", "0042_alter_nominacentroinfancia_talla")
    ]
    (operation,) = migration_0043.Migration.operations
    assert isinstance(operation, migrations.AlterField)
    assert isinstance(operation.field, models.CharField)
    assert operation.field.max_length == 50
