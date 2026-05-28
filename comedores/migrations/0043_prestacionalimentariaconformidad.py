from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("admisiones", "0060_numero_gde_organizacion"),
        ("comedores", "0042_dwecresumentransacciones"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PrestacionAlimentariaConformidad",
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
                ("periodo", models.DateField()),
                ("conforme", models.BooleanField()),
                ("observaciones", models.TextField(blank=True)),
                ("creado", models.DateTimeField(auto_now_add=True)),
                (
                    "comedor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="conformidades_prestacion_alimentaria",
                        to="comedores.comedor",
                    ),
                ),
                (
                    "informe_tecnico",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="conformidades_prestacion_alimentaria",
                        to="admisiones.informetecnico",
                    ),
                ),
                (
                    "usuario",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="conformidades_prestacion_alimentaria",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Conformidad de prestacion alimentaria",
                "verbose_name_plural": "Conformidades de prestaciones alimentarias",
                "ordering": ["-periodo", "-creado"],
            },
        ),
        migrations.AddConstraint(
            model_name="prestacionalimentariaconformidad",
            constraint=models.UniqueConstraint(
                fields=("comedor", "periodo"),
                name="uniq_conformidad_prestacion_alimentaria_mes",
            ),
        ),
    ]
