from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("comunicados", "0006_alter_comunicado_tipo"),
        ("comedores", "0023_alter_comedor_managers_alter_nomina_managers_and_more"),
        ("pwa", "0007_auditoriaoperacionpwa"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="LecturaMensajePWA",
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
                ("visto", models.BooleanField(default=False)),
                ("fecha_visto", models.DateTimeField(blank=True, null=True)),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
                ("fecha_actualizacion", models.DateTimeField(auto_now=True)),
                (
                    "comedor",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="lecturas_mensajes_pwa",
                        to="comedores.comedor",
                    ),
                ),
                (
                    "comunicado",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="lecturas_pwa",
                        to="comunicados.comunicado",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="lecturas_mensajes_pwa",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Lectura mensaje PWA",
                "verbose_name_plural": "Lecturas mensajes PWA",
                "ordering": ("-fecha_visto", "-fecha_creacion", "-id"),
            },
        ),
        migrations.AddConstraint(
            model_name="lecturamensajepwa",
            constraint=models.UniqueConstraint(
                fields=("comunicado", "comedor", "user"),
                name="uniq_lectura_mensaje_pwa_por_usuario_espacio",
            ),
        ),
        migrations.AddIndex(
            model_name="lecturamensajepwa",
            index=models.Index(
                fields=["comedor", "user", "visto"],
                name="pwa_msg_read_com_user_seen_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="lecturamensajepwa",
            index=models.Index(
                fields=["comunicado", "user"],
                name="pwa_msg_read_msg_user_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="lecturamensajepwa",
            index=models.Index(
                fields=["fecha_visto"],
                name="pwa_msg_read_seen_at_idx",
            ),
        ),
    ]
