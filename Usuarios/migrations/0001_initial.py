# Generated by Django 4.0.2 on 2024-08-16 17:07

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Usuarios",
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
                    "imagen",
                    models.ImageField(blank=True, null=True, upload_to="usuarios/"),
                ),
                (
                    "dni",
                    models.PositiveIntegerField(blank=True, null=True, unique=True),
                ),
                ("telefono", models.CharField(blank=True, max_length=30, null=True)),
                ("darkmode", models.BooleanField(blank=True, default=True, null=True)),
                (
                    "usuario",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Usuario",
                "verbose_name_plural": "Usuarios",
                "permissions": [
                    ("rol_directivo", "Directivo"),
                    ("rol_operativo", "Equipo operativo"),
                    ("rol_consultante", "Consultante"),
                    ("rol_observador", "Observador"),
                    ("rol_tecnico", "Equipo técnico"),
                    ("rol_admin", "Administrador"),
                    ("programa_externo", "Externo"),
                    ("programa_CDIF", "CDIF"),
                    ("programa_CDLE", "CDLE"),
                    ("programa_PDV", "PDV"),
                    ("programa_1000D", "1000D"),
                    ("programa_SL", "SL"),
                    ("programa_MA", "MA"),
                    ("programa_Reporte", "Reporte"),
                    ("programa_Administracion", "Administración"),
                    ("programa_Legajo", "Legajo"),
                    ("programa_Configuracion", "Configuración"),
                    ("programa_Dashboard", "Dashboard"),
                ],
            },
        ),
    ]
