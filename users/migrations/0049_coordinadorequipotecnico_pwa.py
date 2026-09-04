# Generated manually for issue #2316.

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        (
            "comedores",
            "0056_imagencomedor_client_uuid_imagencomedor_relevamiento_and_more",
        ),
        ("duplas", "0001_squashed_0003"),
        ("users", "0048_merge_pwa_territorial_and_organizacion"),
    ]

    operations = [
        migrations.CreateModel(
            name="CoordinadorEquipoTecnicoPWA",
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
                ("activo", models.BooleanField(default=True)),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
                ("fecha_actualizacion", models.DateTimeField(auto_now=True)),
                (
                    "comedores_adicionales",
                    models.ManyToManyField(
                        blank=True,
                        related_name="coordinadores_pwa_adicionales",
                        to="comedores.comedor",
                        verbose_name="Comedores adicionales",
                    ),
                ),
                (
                    "duplas",
                    models.ManyToManyField(
                        blank=True,
                        related_name="coordinadores_pwa",
                        to="duplas.dupla",
                        verbose_name="Equipos técnicos",
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=models.deletion.CASCADE,
                        related_name="coordinador_equipo_tecnico_pwa",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Coordinador de equipo técnico PWA",
                "verbose_name_plural": "Coordinadores de equipo técnico PWA",
            },
        ),
        migrations.AddIndex(
            model_name="coordinadorequipotecnicopwa",
            index=models.Index(
                fields=["user", "activo"],
                name="users_coord_user_id_50e688_idx",
            ),
        ),
    ]
