import django.db.models.deletion
from django.db import migrations, models


def _add_plan_estudio_column(apps, schema_editor):
    db = schema_editor.connection
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT DATA_TYPE FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'VAT_tituloreferencia'
        AND COLUMN_NAME = 'plan_estudio_id'
        """
    )
    row = cursor.fetchone()
    if row is None:
        cursor.execute(
            """
            ALTER TABLE `VAT_tituloreferencia`
            ADD COLUMN `plan_estudio_id` bigint NULL
            """
        )
    elif row[0] != "bigint":
        cursor.execute(
            """
            ALTER TABLE `VAT_tituloreferencia`
            MODIFY COLUMN `plan_estudio_id` bigint NULL
            """
        )

    cursor.execute(
        """
        SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'VAT_tituloreferencia'
        AND CONSTRAINT_NAME = 'vat_titulo_plan_estudio_fk'
        AND CONSTRAINT_TYPE = 'FOREIGN KEY'
        """
    )
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            """
            ALTER TABLE `VAT_tituloreferencia`
            ADD CONSTRAINT `vat_titulo_plan_estudio_fk`
            FOREIGN KEY (`plan_estudio_id`)
            REFERENCES `VAT_planversioncurricular` (`id`)
            ON DELETE SET NULL
            """
        )


def _backfill_plan_estudio(apps, schema_editor):
    """Para cada TituloReferencia, asigna el primer Plan que la referenciaba."""
    db = schema_editor.connection
    cursor = db.cursor()
    # Verificar que aún existe titulo_referencia_id en planversioncurricular
    cursor.execute(
        """
        SELECT COUNT(*) FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'VAT_planversioncurricular'
        AND COLUMN_NAME = 'titulo_referencia_id'
        """
    )
    if cursor.fetchone()[0] == 0:
        return  # Ya fue removida, skip backfill
    cursor.execute(
        """
        UPDATE `VAT_tituloreferencia` t
        INNER JOIN (
            SELECT titulo_referencia_id, MIN(id) AS plan_id
            FROM `VAT_planversioncurricular`
            WHERE titulo_referencia_id IS NOT NULL
            GROUP BY titulo_referencia_id
        ) p ON t.id = p.titulo_referencia_id
        SET t.plan_estudio_id = p.plan_id
        WHERE t.plan_estudio_id IS NULL
        """
    )


def _drop_titulo_referencia(apps, schema_editor):
    """Elimina la columna titulo_referencia_id de PlanVersionCurricular."""
    db = schema_editor.connection
    cursor = db.cursor()

    # Buscar y eliminar FK constraints que involucren titulo_referencia_id
    cursor.execute(
        """
        SELECT tc.CONSTRAINT_NAME, tc.CONSTRAINT_TYPE
        FROM information_schema.TABLE_CONSTRAINTS tc
        WHERE tc.TABLE_SCHEMA = DATABASE()
        AND tc.TABLE_NAME = 'VAT_planversioncurricular'
        AND tc.CONSTRAINT_TYPE IN ('UNIQUE', 'FOREIGN KEY')
        """
    )
    constraints = cursor.fetchall()
    for constraint_name, constraint_type in constraints:
        cursor.execute(
            """
            SELECT COUNT(*) FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'VAT_planversioncurricular'
            AND CONSTRAINT_NAME = %s
            AND COLUMN_NAME = 'titulo_referencia_id'
            """,
            [constraint_name],
        )
        if cursor.fetchone()[0] > 0:
            if constraint_type == "FOREIGN KEY":
                cursor.execute(
                    f"ALTER TABLE `VAT_planversioncurricular` "
                    f"DROP FOREIGN KEY `{constraint_name}`"
                )
            elif constraint_type == "UNIQUE":
                cursor.execute(
                    f"ALTER TABLE `VAT_planversioncurricular` "
                    f"DROP INDEX `{constraint_name}`"
                )

    # Eliminar índices restantes sobre titulo_referencia_id
    cursor.execute(
        """
        SELECT DISTINCT INDEX_NAME
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'VAT_planversioncurricular'
        AND COLUMN_NAME = 'titulo_referencia_id'
        AND INDEX_NAME != 'PRIMARY'
        """
    )
    for (index_name,) in cursor.fetchall():
        try:
            cursor.execute(
                f"ALTER TABLE `VAT_planversioncurricular` DROP INDEX `{index_name}`"
            )
        except Exception:
            pass

    # Eliminar columna si existe
    cursor.execute(
        """
        SELECT COUNT(*) FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'VAT_planversioncurricular'
        AND COLUMN_NAME = 'titulo_referencia_id'
        """
    )
    if cursor.fetchone()[0] > 0:
        cursor.execute(
            "ALTER TABLE `VAT_planversioncurricular` "
            "DROP COLUMN `titulo_referencia_id`"
        )


class Migration(migrations.Migration):
    dependencies = [
        ("VAT", "0020_alter_planversioncurricular_options_and_more"),
    ]

    operations = [
        # 1. Actualizar estado Django: quitar unique_together y ordering viejo
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterUniqueTogether(
                    name="planversioncurricular",
                    unique_together=set(),
                ),
                migrations.AlterModelOptions(
                    name="planversioncurricular",
                    options={
                        "ordering": ["sector", "modalidad_cursada"],
                        "verbose_name": "Plan de Estudio",
                        "verbose_name_plural": "Planes de Estudio",
                    },
                ),
            ],
            database_operations=[],
        ),
        # 2. Agregar plan_estudio a TituloReferencia (estado + DB)
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name="tituloreferencia",
                    name="plan_estudio",
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="titulos",
                        to="VAT.planversioncurricular",
                        verbose_name="Plan de Estudio",
                    ),
                ),
            ],
            database_operations=[
                migrations.RunPython(
                    _add_plan_estudio_column, migrations.RunPython.noop
                ),
            ],
        ),
        # 3. Backfill: asignar plan_estudio desde la relación existente
        migrations.RunPython(_backfill_plan_estudio, migrations.RunPython.noop),
        # 4. Eliminar titulo_referencia de PlanVersionCurricular (estado + DB)
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveField(
                    model_name="planversioncurricular",
                    name="titulo_referencia",
                ),
            ],
            database_operations=[
                migrations.RunPython(
                    _drop_titulo_referencia, migrations.RunPython.noop
                ),
            ],
        ),
    ]
