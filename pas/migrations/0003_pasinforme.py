import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("pas", "0002_pas_import_ddjj_tokens"),
    ]

    operations = [
        migrations.CreateModel(
            name="PasInforme",
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
                ("creado", models.DateTimeField(auto_now_add=True)),
                ("filtros", models.JSONField(blank=True, default=dict)),
                ("modo", models.CharField(default="registros", max_length=20)),
                ("resultado", models.JSONField(blank=True, default=list)),
                ("total_personas", models.PositiveIntegerField(default=0)),
                ("total_cambios", models.PositiveIntegerField(default=0)),
                (
                    "cambios",
                    models.ManyToManyField(
                        blank=True,
                        related_name="informes",
                        to="pas.pashistorialestado",
                    ),
                ),
                (
                    "personas",
                    models.ManyToManyField(
                        blank=True,
                        related_name="informes",
                        to="pas.paspersona",
                    ),
                ),
                (
                    "usuario",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="informes_pas",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Informe PAS",
                "verbose_name_plural": "Informes PAS",
                "ordering": ["-creado", "-id"],
            },
        ),
    ]
