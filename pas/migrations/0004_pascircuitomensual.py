import django.db.models.deletion
import pas.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("pas", "0003_pasinforme"),
    ]

    operations = [
        migrations.CreateModel(
            name="PasCircuitoMensual",
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
                ("periodo", models.DateField(unique=True)),
                (
                    "fecha_exportacion_sintys",
                    models.DateTimeField(blank=True, null=True),
                ),
                (
                    "archivo_exportacion_sintys",
                    models.FileField(
                        blank=True,
                        null=True,
                        upload_to=pas.models.archivo_circuito_pas_upload_to,
                    ),
                ),
                (
                    "fecha_importacion_sintys",
                    models.DateTimeField(blank=True, null=True),
                ),
                (
                    "archivo_retorno_sintys",
                    models.FileField(
                        blank=True,
                        null=True,
                        upload_to=pas.models.archivo_circuito_pas_upload_to,
                    ),
                ),
                (
                    "fecha_cruce_justicia",
                    models.DateTimeField(blank=True, null=True),
                ),
                (
                    "fecha_cruce_migraciones",
                    models.DateTimeField(blank=True, null=True),
                ),
                (
                    "fecha_procesamiento_alertas",
                    models.DateTimeField(blank=True, null=True),
                ),
                ("fecha_cierre", models.DateTimeField(blank=True, null=True)),
                (
                    "exportado_por",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="circuitos_pas_exportados",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "importado_por",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="circuitos_pas_importados",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Circuito mensual PAS",
                "verbose_name_plural": "Circuitos mensuales PAS",
                "ordering": ["-periodo"],
            },
        ),
    ]
