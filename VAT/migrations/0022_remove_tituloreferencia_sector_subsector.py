import django.db.models.deletion
from django.db import migrations


def _drop_titulo_sector_subsector(apps, schema_editor):
    cursor = schema_editor.connection.cursor()

    cursor.execute(
        """
        SELECT tc.CONSTRAINT_NAME
        FROM information_schema.TABLE_CONSTRAINTS tc
        INNER JOIN information_schema.KEY_COLUMN_USAGE kcu
            ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
            AND tc.TABLE_SCHEMA = kcu.TABLE_SCHEMA
            AND tc.TABLE_NAME = kcu.TABLE_NAME
        WHERE tc.TABLE_SCHEMA = DATABASE()
        AND tc.TABLE_NAME = 'VAT_tituloreferencia'
        AND tc.CONSTRAINT_TYPE = 'FOREIGN KEY'
        AND kcu.COLUMN_NAME IN ('sector_id', 'subsector_id')
        """
    )
    for (constraint_name,) in cursor.fetchall():
        cursor.execute(
            f"ALTER TABLE `VAT_tituloreferencia` DROP FOREIGN KEY `{constraint_name}`"
        )

    cursor.execute(
        """
        SELECT DISTINCT INDEX_NAME
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'VAT_tituloreferencia'
        AND COLUMN_NAME IN ('sector_id', 'subsector_id')
        AND INDEX_NAME != 'PRIMARY'
        """
    )
    for (index_name,) in cursor.fetchall():
        cursor.execute(
            f"ALTER TABLE `VAT_tituloreferencia` DROP INDEX `{index_name}`"
        )

    for column_name in ("sector_id", "subsector_id"):
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'VAT_tituloreferencia'
            AND COLUMN_NAME = %s
            """,
            [column_name],
        )
        if cursor.fetchone()[0] > 0:
            cursor.execute(
                f"ALTER TABLE `VAT_tituloreferencia` DROP COLUMN `{column_name}`"
            )


class Migration(migrations.Migration):
    dependencies = [
        ("VAT", "0021_invert_titulo_plan_relation"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveField(
                    model_name="tituloreferencia",
                    name="sector",
                ),
                migrations.RemoveField(
                    model_name="tituloreferencia",
                    name="subsector",
                ),
            ],
            database_operations=[
                migrations.RunPython(
                    _drop_titulo_sector_subsector,
                    reverse_code=migrations.RunPython.noop,
                ),
            ],
        ),
    ]