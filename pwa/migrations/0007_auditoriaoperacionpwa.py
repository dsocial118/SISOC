from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("comedores", "0023_alter_comedor_managers_alter_nomina_managers_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("pwa", "0006_nominaespaciopwa"),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditoriaOperacionPWA",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("entidad", models.CharField(db_index=True, max_length=50)),
                ("entidad_id", models.PositiveIntegerField(db_index=True)),
                (
                    "accion",
                    models.CharField(
                        choices=[
                            ("create", "Alta"),
                            ("update", "Edicion"),
                            ("delete", "Baja"),
                            ("activate", "Reactivacion"),
                            ("deactivate", "Desactivacion"),
                        ],
                        db_index=True,
                        max_length=20,
                    ),
                ),
                ("fecha_evento", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("snapshot_antes", models.JSONField(blank=True, null=True)),
                ("snapshot_despues", models.JSONField(blank=True, null=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                (
                    "comedor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="auditorias_operacion_pwa",
                        to="comedores.comedor",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="auditorias_operacion_pwa",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Auditoria operacion PWA",
                "verbose_name_plural": "Auditorias operaciones PWA",
            },
        ),
        migrations.AddIndex(
            model_name="auditoriaoperacionpwa",
            index=models.Index(fields=["comedor", "fecha_evento"], name="pwa_auditor_comedor_7aab3b_idx"),
        ),
        migrations.AddIndex(
            model_name="auditoriaoperacionpwa",
            index=models.Index(
                fields=["entidad", "entidad_id", "fecha_evento"],
                name="pwa_auditor_entidad_206fc7_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="auditoriaoperacionpwa",
            index=models.Index(fields=["accion", "fecha_evento"], name="pwa_auditor_accion_ee36b2_idx"),
        ),
    ]
