from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("centrodeinfancia", "0011_alter_formulariocdi_electrical_safety_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Trabajador",
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
                ("deleted_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                (
                    "nombre",
                    models.CharField(max_length=255),
                ),
                (
                    "apellido",
                    models.CharField(max_length=255),
                ),
                (
                    "telefono",
                    models.CharField(blank=True, max_length=50, null=True),
                ),
                (
                    "rol",
                    models.CharField(
                        choices=[
                            ("profesor", "Profesor"),
                            ("director", "Director"),
                            ("administrativo", "Administrativo"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "deleted_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="auth.user",
                    ),
                ),
                (
                    "centro",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="trabajadores",
                        to="centrodeinfancia.centrodeinfancia",
                    ),
                ),
            ],
            options={
                "verbose_name": "Trabajador",
                "verbose_name_plural": "Trabajadores",
                "ordering": ["apellido", "nombre"],
            },
        ),
    ]
