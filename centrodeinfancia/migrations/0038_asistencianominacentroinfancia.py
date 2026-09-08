# Generated manually for issue #2092.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("centrodeinfancia", "0037_trabajador_usuario"),
    ]

    operations = [
        migrations.CreateModel(
            name="AsistenciaNominaCentroInfancia",
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
                ("fecha", models.DateField(verbose_name="Fecha")),
                (
                    "presente",
                    models.BooleanField(default=False, verbose_name="Presente"),
                ),
                (
                    "observaciones",
                    models.TextField(
                        blank=True,
                        null=True,
                        verbose_name="Observaciones",
                    ),
                ),
                (
                    "fecha_registro",
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name="Fecha de registro",
                    ),
                ),
                (
                    "nomina",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="asistencias_nomina",
                        to="centrodeinfancia.nominacentroinfancia",
                        verbose_name="Nómina",
                    ),
                ),
                (
                    "registrado_por",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="asistencias_nomina_cdi_registradas",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Registrado por",
                    ),
                ),
            ],
            options={
                "verbose_name": "Asistencia de nómina CDI",
                "verbose_name_plural": "Asistencias de nómina CDI",
                "ordering": ["-fecha"],
            },
        ),
        migrations.AddConstraint(
            model_name="asistencianominacentroinfancia",
            constraint=models.UniqueConstraint(
                fields=("nomina", "fecha"),
                name="uniq_cdi_asist_nomina_fecha",
            ),
        ),
        migrations.AddIndex(
            model_name="asistencianominacentroinfancia",
            index=models.Index(
                fields=["fecha", "presente"],
                name="cdi_asist_nom_fecha_idx",
            ),
        ),
    ]
