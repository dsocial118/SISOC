from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("comedores", "0034_merge_20260329_0001"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("pwa", "0008_lecturamensajepwa"),
    ]

    operations = [
        migrations.CreateModel(
            name="RegistroAsistenciaNominaPWA",
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
                    "periodicidad",
                    models.CharField(
                        choices=[("mensual", "Mensual")],
                        default="mensual",
                        max_length=20,
                    ),
                ),
                (
                    "periodo_referencia",
                    models.DateField(
                        help_text=(
                            "Fecha ancla del período. Para mensual se usa "
                            "el primer día del mes."
                        )
                    ),
                ),
                (
                    "fecha_toma_asistencia",
                    models.DateTimeField(auto_now_add=True, db_index=True),
                ),
                ("metadata", models.JSONField(blank=True, default=dict)),
                (
                    "nomina",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="registros_asistencia_pwa",
                        to="comedores.nomina",
                    ),
                ),
                (
                    "tomado_por",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="asistencias_nomina_pwa_registradas",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Registro Asistencia Nómina PWA",
                "verbose_name_plural": "Registros Asistencia Nómina PWA",
                "ordering": ("-periodo_referencia", "-fecha_toma_asistencia", "-id"),
            },
        ),
        migrations.AddConstraint(
            model_name="registroasistencianominapwa",
            constraint=models.UniqueConstraint(
                fields=("nomina", "periodicidad", "periodo_referencia"),
                name="uniq_pwa_asistencia_nomina_periodo",
            ),
        ),
        migrations.AddIndex(
            model_name="registroasistencianominapwa",
            index=models.Index(
                fields=["nomina", "periodicidad", "periodo_referencia"],
                name="pwa_nom_asis_nom_per_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="registroasistencianominapwa",
            index=models.Index(
                fields=["periodicidad", "periodo_referencia"],
                name="pwa_nom_asis_periodo_idx",
            ),
        ),
    ]
