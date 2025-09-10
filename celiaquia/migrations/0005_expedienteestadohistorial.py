# Generated manually for ExpedienteEstadoHistorial model
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("celiaquia", "0004_pagoexpediente_pagonomina_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="ExpedienteEstadoHistorial",
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
                ("fecha", models.DateTimeField(auto_now_add=True)),
                ("observaciones", models.TextField(blank=True, null=True)),
                (
                    "expediente",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="historial",
                        to="celiaquia.expediente",
                    ),
                ),
                (
                    "estado_anterior",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="celiaquia.estadoexpediente",
                    ),
                ),
                (
                    "estado_nuevo",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="celiaquia.estadoexpediente",
                    ),
                ),
                (
                    "usuario",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="cambios_estado",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Historial de estado",
                "verbose_name_plural": "Historial de estados",
                "ordering": ("-fecha",),
            },
        ),
    ]
