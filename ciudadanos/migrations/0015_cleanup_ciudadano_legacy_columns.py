from django.db import migrations


def drop_legacy_columns(apps, schema_editor):
    """
    Remove leftover columns that were dropped in state but can still exist in
    MySQL with NOT NULL/no default (e.g. demo_centro_familia). This makes
    inserts align with the current model definition.
    """

    connection = schema_editor.connection
    if connection.vendor == "sqlite":
        return
    quote = schema_editor.quote_name
    table = "ciudadanos_ciudadano"

    def table_exists(name: str) -> bool:
        with connection.cursor() as cursor:
            return name in set(connection.introspection.table_names(cursor))

    if not table_exists(table):
        return

    def column_exists(column: str) -> bool:
        with connection.cursor() as cursor:
            columns = connection.introspection.get_table_description(cursor, table)
        return any(col.name == column for col in columns)

    def drop_fk_constraints(column: str) -> None:
        with connection.cursor() as cursor:
            constraints = connection.introspection.get_constraints(cursor, table)
        for name, details in constraints.items():
            if column in details.get("columns", []) and details.get("foreign_key"):
                schema_editor.execute(
                    f"ALTER TABLE {quote(table)} DROP FOREIGN KEY {quote(name)}"
                )

    def drop_column_if_exists(column: str) -> None:
        if not column_exists(column):
            return
        drop_fk_constraints(column)
        schema_editor.execute(
            f"ALTER TABLE {quote(table)} DROP COLUMN {quote(column)}"
        )

    # Columns that were removed in state but might remain in legacy DBs.
    legacy_columns = [
        "demo_centro_familia",  # boolean, previously misnamed as *_id in cleanup
        "demo_centro_familia_id",
        "estado",  # fallback in case 0014 wasn't enough
        "estado_id",
        "circuito_id",
        "escalera_manzana",
        "torre_pasillo",
        # latitud/longitud/estado_civil_id se preservan para migrar datos en 0016.
    ]

    for column in legacy_columns:
        drop_column_if_exists(column)


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("ciudadanos", "0014_remove_ciudadano_estado_column"),
    ]

    operations = [
        migrations.RunPython(drop_legacy_columns, migrations.RunPython.noop),
    ]
