from django.db import migrations


def ensure_grupofamiliar_text_fields(apps, schema_editor):
    """
    Aligns the GrupoFamiliar schema with the current CharField definitions.
    MySQL still had legacy FK columns (vinculo_id/estado_relacion_id) because
    migration 0009 only updated the state. This creates the expected varchar
    columns, copies data when the old lookup tables are available, and drops
    the FK columns so Django can read/write without hitting missing columns.
    """

    connection = schema_editor.connection
    if connection.vendor != "mysql":
        return

    quote = schema_editor.quote_name

    def table_exists(name: str) -> bool:
        with connection.cursor() as cursor:
            return name in set(connection.introspection.table_names(cursor))

    def column_exists(table: str, column: str) -> bool:
        if not table_exists(table):
            return False
        with connection.cursor() as cursor:
            return column in [
                col.name
                for col in connection.introspection.get_table_description(
                    cursor, table
                )
            ]

    def add_column_if_missing(table: str, column: str, definition_sql: str) -> None:
        if table_exists(table) and not column_exists(table, column):
            schema_editor.execute(
                f"ALTER TABLE {quote(table)} ADD COLUMN {definition_sql}"
            )

    def drop_fk_constraints(table: str, column: str) -> None:
        if not table_exists(table):
            return
        with connection.cursor() as cursor:
            constraints = connection.introspection.get_constraints(cursor, table)
        for name, details in constraints.items():
            if column in details.get("columns", []) and details.get("foreign_key"):
                schema_editor.execute(
                    f"ALTER TABLE {quote(table)} DROP FOREIGN KEY {quote(name)}"
                )

    def drop_unique_constraints(table: str, column: str) -> None:
        if not table_exists(table):
            return
        with connection.cursor() as cursor:
            constraints = connection.introspection.get_constraints(cursor, table)
        for name, details in constraints.items():
            if details.get("unique") and column in details.get("columns", []):
                schema_editor.execute(
                    f"ALTER TABLE {quote(table)} DROP INDEX {quote(name)}"
                )

    def drop_column_if_exists(table: str, column: str) -> None:
        if table_exists(table) and column_exists(table, column):
            schema_editor.execute(
                f"ALTER TABLE {quote(table)} DROP COLUMN {quote(column)}"
            )

    table = "ciudadanos_grupofamiliar"

    add_column_if_missing(
        table,
        "vinculo",
        f"{quote('vinculo')} VARCHAR(20) NULL",
    )
    add_column_if_missing(
        table,
        "estado_relacion",
        f"{quote('estado_relacion')} VARCHAR(20) NULL",
    )

    if column_exists(table, "vinculo") and column_exists(table, "vinculo_id"):
        if table_exists("ciudadanos_vinculofamiliar"):
            schema_editor.execute(
                f"""
                UPDATE {quote(table)} gf
                LEFT JOIN {quote("ciudadanos_vinculofamiliar")} vf
                    ON gf.{quote("vinculo_id")} = vf.{quote("id")}
                SET gf.{quote("vinculo")} = COALESCE(gf.{quote("vinculo")}, vf.{quote("vinculo")})
                WHERE gf.{quote("vinculo")} IS NULL;
                """
            )
        drop_fk_constraints(table, "vinculo_id")
        drop_unique_constraints(table, "vinculo_id")
        drop_column_if_exists(table, "vinculo_id")

    if column_exists(table, "estado_relacion") and column_exists(
        table, "estado_relacion_id"
    ):
        if table_exists("ciudadanos_estadorelacion"):
            schema_editor.execute(
                f"""
                UPDATE {quote(table)} gf
                LEFT JOIN {quote("ciudadanos_estadorelacion")} er
                    ON gf.{quote("estado_relacion_id")} = er.{quote("id")}
                SET gf.{quote("estado_relacion")} = COALESCE(gf.{quote("estado_relacion")}, er.{quote("estado")})
                WHERE gf.{quote("estado_relacion")} IS NULL;
                """
            )
        drop_fk_constraints(table, "estado_relacion_id")
        drop_unique_constraints(table, "estado_relacion_id")
        drop_column_if_exists(table, "estado_relacion_id")


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("ciudadanos", "0012_fix_ciudadano_datetime_fields"),
    ]

    operations = [
        migrations.RunPython(
            ensure_grupofamiliar_text_fields,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
