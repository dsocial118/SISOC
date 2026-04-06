from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("rendicioncuentasmensual", "0003_alter_documentacionadjunta_related_name_archivos_adjuntos"),
    ]

    operations = [
        migrations.AddField(
            model_name="rendicioncuentamensual",
            name="convenio",
            field=models.CharField(
                blank=True,
                max_length=100,
                null=True,
                verbose_name="Convenio",
            ),
        ),
        migrations.AddField(
            model_name="rendicioncuentamensual",
            name="estado",
            field=models.CharField(
                choices=[
                    ("elaboracion", "Presentación en elaboración"),
                    ("revision", "Presentación en revisión"),
                    ("subsanar", "Presentación a subsanar"),
                    ("finalizada", "Presentación finalizada"),
                ],
                default="elaboracion",
                max_length=20,
                verbose_name="Estado de Rendición",
            ),
        ),
        migrations.AddField(
            model_name="rendicioncuentamensual",
            name="numero_rendicion",
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                verbose_name="Número de Rendición",
            ),
        ),
        migrations.AddField(
            model_name="rendicioncuentamensual",
            name="periodo_fin",
            field=models.DateField(
                blank=True,
                null=True,
                verbose_name="Período fin",
            ),
        ),
        migrations.AddField(
            model_name="rendicioncuentamensual",
            name="periodo_inicio",
            field=models.DateField(
                blank=True,
                null=True,
                verbose_name="Período inicio",
            ),
        ),
    ]
