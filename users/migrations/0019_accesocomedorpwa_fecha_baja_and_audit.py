from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("comedores", "0032_merge_20260326_1545"),
        ("organizaciones", "0001_initial"),
        ("users", "0018_profile_temporary_password_plaintext"),
    ]

    operations = [
        migrations.AddField(
            model_name="accesocomedorpwa",
            name="fecha_baja",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name="AuditAccesoComedorPWA",
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
                            ("reactivate", "Reactivación"),
                            ("deactivate", "Baja"),
                        ],
                        db_index=True,
                        max_length=20,
                    ),
                ),
                ("fecha_evento", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                (
                    "acceso",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="audit_logs",
                        to="users.accesocomedorpwa",
                    ),
                ),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="accesos_pwa_audit_eventos",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "comedor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="accesos_pwa_audit_logs",
                        to="comedores.comedor",
                    ),
                ),
                (
                    "organizacion",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="accesos_pwa_audit_logs",
                        to="organizaciones.organizacion",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="accesos_pwa_audit_logs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Auditoría de acceso PWA",
                "verbose_name_plural": "Auditorías de accesos PWA",
                "ordering": ["-fecha_evento", "-id"],
            },
        ),
        migrations.AddIndex(
            model_name="auditaccesocomedorpwa",
            index=models.Index(fields=["user", "fecha_evento"], name="users_audit_user_74b57d_idx"),
        ),
        migrations.AddIndex(
            model_name="auditaccesocomedorpwa",
            index=models.Index(fields=["comedor", "fecha_evento"], name="users_audit_comedor_4b01f7_idx"),
        ),
        migrations.AddIndex(
            model_name="auditaccesocomedorpwa",
            index=models.Index(fields=["accion", "fecha_evento"], name="users_audit_accion_9d4c59_idx"),
        ),
    ]
