from django.db import migrations


def _drop_curso_columns_if_present(apps, schema_editor):
    """Drop legacy Curso columns only when they exist (MySQL-compatible)."""
    table_name = "VAT_curso"
    columns = ("cupo_total", "fecha_inicio", "fecha_fin")

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(f"SHOW COLUMNS FROM `{table_name}`")
        existing = {row[0] for row in cursor.fetchall()}

        for column_name in columns:
            if column_name in existing:
                cursor.execute(
                    f"ALTER TABLE `{table_name}` DROP COLUMN `{column_name}`"
                )


class Migration(migrations.Migration):
    dependencies = [
        ("VAT", "0023_ofertainstitucional_voucher_parametrias"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    _drop_curso_columns_if_present,
                    reverse_code=migrations.RunPython.noop,
                )
            ],
            state_operations=[
                migrations.RemoveField(
                    model_name="curso",
                    name="cupo_total",
                ),
                migrations.RemoveField(
                    model_name="curso",
                    name="fecha_fin",
                ),
                migrations.RemoveField(
                    model_name="curso",
                    name="fecha_inicio",
                ),
            ],
        ),
    ]
