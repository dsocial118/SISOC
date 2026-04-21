import core.soft_delete
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import duplas.models


class Migration(migrations.Migration):

    replaces = [
        ("duplas", "0001_initial"),
        ("duplas", "0002_dupla_coordinador"),
        ("duplas", "0003_alter_dupla_managers_dupla_deleted_at_and_more"),
    ]

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Dupla",
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
                ("nombre", models.CharField(max_length=255)),
                (
                    "estado",
                    models.CharField(
                        choices=[("Activo", "Activo"), ("Inactivo", "Inactivo")],
                        max_length=50,
                    ),
                ),
                ("fecha", models.DateTimeField(auto_now_add=True)),
                (
                    "deleted_at",
                    models.DateTimeField(blank=True, db_index=True, null=True),
                ),
                (
                    "abogado",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "coordinador",
                    models.ForeignKey(
                        blank=True,
                        help_text="Coordinador asignado a esta dupla. Si se elimina el coordinador, este campo quedará vacío.",
                        limit_choices_to={"groups__name": "Coordinador Equipo Tecnico"},
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="duplas_coordinadas",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Coordinador de Equipo Técnico",
                    ),
                ),
                (
                    "deleted_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "tecnico",
                    models.ManyToManyField(
                        related_name="dupla_tecnico", to=settings.AUTH_USER_MODEL
                    ),
                ),
            ],
            managers=[
                ("objects", duplas.models.DuplaManager()),
                ("all_objects", core.soft_delete.SoftDeleteManager(include_deleted=True)),
            ],
        ),
    ]
