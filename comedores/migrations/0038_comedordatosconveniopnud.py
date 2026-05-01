from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("comedores", "0037_imagencomedor_origen"),
    ]

    operations = [
        migrations.CreateModel(
            name="ComedorDatosConvenioPnud",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "monto_total_conveniado",
                    models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True),
                ),
                ("nro_convenio", models.CharField(blank=True, max_length=120, null=True)),
                (
                    "monto_total_convenio_por_espacio",
                    models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True),
                ),
                (
                    "prestaciones_financiadas_mensuales",
                    models.PositiveIntegerField(blank=True, null=True),
                ),
                ("personas_conveniadas", models.PositiveIntegerField(blank=True, null=True)),
                ("cantidad_modulos", models.PositiveIntegerField(blank=True, null=True)),
                ("actualizado_en", models.DateTimeField(auto_now=True)),
                (
                    "comedor",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="datos_convenio_pnud",
                        to="comedores.comedor",
                    ),
                ),
            ],
            options={
                "verbose_name": "Datos del Convenio PNUD",
                "verbose_name_plural": "Datos del Convenio PNUD",
            },
        ),
    ]
