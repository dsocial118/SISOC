import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditoriaSesionPWA",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("username_intentado", models.CharField(blank=True, max_length=150, null=True)),
                (
                    "evento",
                    models.CharField(
                        choices=[
                            ("login_ok", "Login exitoso"),
                            ("login_error", "Login fallido"),
                            ("logout", "Logout"),
                            ("token_invalido", "Token inválido"),
                            ("me_ok", "Consulta de contexto"),
                        ],
                        max_length=30,
                    ),
                ),
                (
                    "resultado",
                    models.CharField(choices=[("ok", "OK"), ("error", "Error")], max_length=10),
                ),
                ("fecha_evento", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("ip", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.CharField(blank=True, max_length=512, null=True)),
                ("path", models.CharField(max_length=255)),
                ("metodo_http", models.CharField(max_length=10)),
                ("codigo_respuesta", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("motivo_error", models.CharField(blank=True, max_length=255, null=True)),
                ("session_id", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False)),
                ("rol_pwa_snapshot", models.JSONField(blank=True, default=list)),
                ("comedor_ids_snapshot", models.JSONField(blank=True, default=list)),
                ("app_version", models.CharField(blank=True, max_length=50, null=True)),
                ("platform", models.CharField(blank=True, max_length=30, null=True)),
                ("is_standalone", models.BooleanField(blank=True, null=True)),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="auditorias_pwa",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Auditoría sesión PWA",
                "verbose_name_plural": "Auditorías sesiones PWA",
            },
        ),
        migrations.AddIndex(
            model_name="auditoriasesionpwa",
            index=models.Index(fields=["user", "fecha_evento"], name="pwa_auditor_user_id_52e452_idx"),
        ),
        migrations.AddIndex(
            model_name="auditoriasesionpwa",
            index=models.Index(fields=["evento", "fecha_evento"], name="pwa_auditor_evento_49cf48_idx"),
        ),
        migrations.AddIndex(
            model_name="auditoriasesionpwa",
            index=models.Index(fields=["resultado", "fecha_evento"], name="pwa_auditor_resulta_2d6494_idx"),
        ),
    ]
