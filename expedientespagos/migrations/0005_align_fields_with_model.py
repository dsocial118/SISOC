from django.db import migrations, models


def fill_nulls(apps, schema_editor):
    connection = schema_editor.connection
    table = 'expedientespagos_expedientepago'
    statements = [
        f"UPDATE `{table}` SET prestaciones_mensuales_desayuno = 0 WHERE prestaciones_mensuales_desayuno IS NULL",
        f"UPDATE `{table}` SET prestaciones_mensuales_almuerzo = 0 WHERE prestaciones_mensuales_almuerzo IS NULL",
        f"UPDATE `{table}` SET prestaciones_mensuales_merienda = 0 WHERE prestaciones_mensuales_merienda IS NULL",
        f"UPDATE `{table}` SET prestaciones_mensuales_cena = 0 WHERE prestaciones_mensuales_cena IS NULL",
        f"UPDATE `{table}` SET monto_mensual_desayuno = 0 WHERE monto_mensual_desayuno IS NULL",
        f"UPDATE `{table}` SET monto_mensual_almuerzo = 0 WHERE monto_mensual_almuerzo IS NULL",
        f"UPDATE `{table}` SET monto_mensual_merienda = 0 WHERE monto_mensual_merienda IS NULL",
        f"UPDATE `{table}` SET monto_mensual_cena = 0 WHERE monto_mensual_cena IS NULL",
        f"UPDATE `{table}` SET ano = '' WHERE ano IS NULL",
        f"UPDATE `{table}` SET expediente_convenio = '' WHERE expediente_convenio IS NULL",
    ]
    with connection.cursor() as cursor:
        for sql in statements:
            try:
                cursor.execute(sql)
            except Exception:
                # If column doesn't exist in this environment, skip silently
                pass


class Migration(migrations.Migration):

    dependencies = [
        ('expedientespagos', '0004_merge_20260203_1249'),
    ]

    operations = [
        migrations.RunPython(fill_nulls, migrations.RunPython.noop),
        # Bring state in sync for monthly fields without re-adding columns
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='expedientepago',
                    name='prestaciones_mensuales_desayuno',
                    field=models.IntegerField(verbose_name='Prestaciones mensuales desayuno'),
                ),
                migrations.AddField(
                    model_name='expedientepago',
                    name='prestaciones_mensuales_almuerzo',
                    field=models.IntegerField(verbose_name='Prestaciones mensuales almuerzo'),
                ),
                migrations.AddField(
                    model_name='expedientepago',
                    name='prestaciones_mensuales_merienda',
                    field=models.IntegerField(verbose_name='Prestaciones mensuales merienda'),
                ),
                migrations.AddField(
                    model_name='expedientepago',
                    name='prestaciones_mensuales_cena',
                    field=models.IntegerField(verbose_name='Prestaciones mensuales cena'),
                ),
                migrations.AddField(
                    model_name='expedientepago',
                    name='monto_mensual_desayuno',
                    field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Monto mensual desayuno'),
                ),
                migrations.AddField(
                    model_name='expedientepago',
                    name='monto_mensual_almuerzo',
                    field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Monto mensual almuerzo'),
                ),
                migrations.AddField(
                    model_name='expedientepago',
                    name='monto_mensual_merienda',
                    field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Monto mensual merienda'),
                ),
                migrations.AddField(
                    model_name='expedientepago',
                    name='monto_mensual_cena',
                    field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Monto mensual cena'),
                ),
            ],
            database_operations=[],
        ),
        # Ensure DB columns are NOT NULL as per model
        migrations.RunSQL("ALTER TABLE `expedientespagos_expedientepago` MODIFY `monto_mensual_desayuno` DECIMAL(10,2) NOT NULL", migrations.RunSQL.noop),
        migrations.RunSQL("ALTER TABLE `expedientespagos_expedientepago` MODIFY `monto_mensual_almuerzo` DECIMAL(10,2) NOT NULL", migrations.RunSQL.noop),
        migrations.RunSQL("ALTER TABLE `expedientespagos_expedientepago` MODIFY `monto_mensual_merienda` DECIMAL(10,2) NOT NULL", migrations.RunSQL.noop),
        migrations.RunSQL("ALTER TABLE `expedientespagos_expedientepago` MODIFY `monto_mensual_cena` DECIMAL(10,2) NOT NULL", migrations.RunSQL.noop),
        migrations.RunSQL("ALTER TABLE `expedientespagos_expedientepago` MODIFY `prestaciones_mensuales_desayuno` INT NOT NULL", migrations.RunSQL.noop),
        migrations.RunSQL("ALTER TABLE `expedientespagos_expedientepago` MODIFY `prestaciones_mensuales_almuerzo` INT NOT NULL", migrations.RunSQL.noop),
        migrations.RunSQL("ALTER TABLE `expedientespagos_expedientepago` MODIFY `prestaciones_mensuales_merienda` INT NOT NULL", migrations.RunSQL.noop),
        migrations.RunSQL("ALTER TABLE `expedientespagos_expedientepago` MODIFY `prestaciones_mensuales_cena` INT NOT NULL", migrations.RunSQL.noop),
        migrations.RunSQL("ALTER TABLE `expedientespagos_expedientepago` MODIFY `ano` VARCHAR(4) NOT NULL", migrations.RunSQL.noop),
        migrations.RunSQL("ALTER TABLE `expedientespagos_expedientepago` MODIFY `expediente_convenio` VARCHAR(255) NOT NULL", migrations.RunSQL.noop),
    ]
