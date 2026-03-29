from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("comedores", "0030_colaboradores_espacio"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="colaboradorespacio",
            name="uniq_colaborador_espacio_por_comedor_ciudadano",
        ),
        migrations.CreateModel(
            name="AuditColaboradorEspacio",
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
                    "accion",
                    models.CharField(
                        choices=[
                            ("create", "Alta"),
                            ("update", "Edición"),
                            ("delete", "Baja"),
                        ],
                        db_index=True,
                        max_length=20,
                    ),
                ),
                ("changed_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("snapshot_antes", models.JSONField(blank=True, null=True)),
                ("snapshot_despues", models.JSONField(blank=True, null=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                (
                    "changed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="colaboradores_espacio_audit_logs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "ciudadano",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="colaboraciones_audit_logs",
                        to="ciudadanos.ciudadano",
                    ),
                ),
                (
                    "colaborador",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="audit_logs",
                        to="comedores.colaboradorespacio",
                    ),
                ),
                (
                    "comedor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="colaboradores_audit_logs",
                        to="comedores.comedor",
                    ),
                ),
            ],
            options={
                "verbose_name": "Auditoría de colaborador del espacio",
                "verbose_name_plural": "Auditorías de colaboradores del espacio",
                "ordering": ["-changed_at", "-id"],
                "indexes": [
                    models.Index(
                        fields=["comedor", "changed_at"],
                        name="comedores_a_comedor_89ef7d_idx",
                    ),
                    models.Index(
                        fields=["ciudadano", "changed_at"],
                        name="comedores_a_ciudada_b3ff72_idx",
                    ),
                    models.Index(
                        fields=["accion", "changed_at"],
                        name="comedores_a_accion_825919_idx",
                    ),
                ],
            },
        ),
    ]
