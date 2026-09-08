from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "rendicioncuentasmensual",
            "0013_alter_documentacionadjunta_categoria_choices",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="rendicioncuentamensual",
            name="etapa_proceso",
            field=models.CharField(
                choices=[
                    ("carga_documentacion", "Carga de documentación"),
                    ("revision_documentacion", "Revisión Territorial"),
                    ("revision_auditoria", "Revisión de Auditoría"),
                    ("auditoria", "Auditoría"),
                    ("regularizacion", "Regularización"),
                ],
                default="carga_documentacion",
                max_length=30,
                verbose_name="Etapa del proceso",
            ),
        ),
        migrations.AddField(
            model_name="rendicioncuentamensual",
            name="subestado_proceso",
            field=models.CharField(
                choices=[
                    ("pendiente", "Pendiente"),
                    ("en_curso", "En curso"),
                    ("pendiente_correcciones", "Pendiente de correcciones"),
                    ("subsanado", "Subsanado"),
                    ("finalizada", "Finalizada"),
                    ("finalizada_con_observaciones", "Finalizada con observaciones"),
                ],
                default="en_curso",
                max_length=35,
                verbose_name="Subestado del proceso",
            ),
        ),
        migrations.AddField(
            model_name="rendicioncuentamensual",
            name="monto_rendido",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=15,
                null=True,
                verbose_name="Monto rendido",
            ),
        ),
        migrations.AddField(
            model_name="rendicioncuentamensual",
            name="fecha_validacion_territorial",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="rendicioncuentamensual",
            name="fecha_validacion_auditoria",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="rendicioncuentamensual",
            name="fecha_carga_auditoria",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="rendicioncuentamensual",
            name="fecha_auditada",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="rendicioncuentamensual",
            name="acta_auditoria",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to="rendicioncuentasmensual/auditoria/actas/",
                verbose_name="PDF Acta de Auditoría",
            ),
        ),
        migrations.AddField(
            model_name="rendicioncuentamensual",
            name="fecha_regularizacion",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="rendicioncuentamensual",
            name="documento_regularizacion",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to="rendicioncuentasmensual/auditoria/regularizaciones/",
                verbose_name="PDF Regularización",
            ),
        ),
    ]
