import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("pas", "0004_pascircuitomensual"),
    ]

    operations = [
        migrations.CreateModel(
            name="PasControlRenaper",
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
                ("fecha_consulta", models.DateField()),
                ("consultado", models.DateTimeField(auto_now_add=True)),
                (
                    "resultado",
                    models.CharField(
                        choices=[
                            ("vigente", "Persona viva"),
                            ("fallecida", "Persona fallecida"),
                            ("no_encontrada", "Sin coincidencia"),
                            ("error", "Error de consulta"),
                        ],
                        max_length=20,
                    ),
                ),
                ("sexo_consulta", models.CharField(blank=True, max_length=1)),
                ("error_tipo", models.CharField(blank=True, max_length=40)),
                (
                    "persona",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="controles_renaper",
                        to="pas.paspersona",
                    ),
                ),
            ],
            options={
                "verbose_name": "Control RENAPER PAS",
                "verbose_name_plural": "Controles RENAPER PAS",
                "ordering": ["-fecha_consulta", "persona_id"],
            },
        ),
        migrations.CreateModel(
            name="PasIncompatibilidad",
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
                    "categoria",
                    models.CharField(
                        choices=[("supervivencia", "Supervivencia")],
                        max_length=30,
                    ),
                ),
                ("periodo_impacto", models.DateField()),
                ("fecha_deteccion", models.DateTimeField(auto_now_add=True)),
                ("detalle", models.CharField(max_length=255)),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("pendiente", "Pendiente"),
                            ("gestionada", "Gestionada"),
                        ],
                        default="pendiente",
                        max_length=20,
                    ),
                ),
                (
                    "persona",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="incompatibilidades",
                        to="pas.paspersona",
                    ),
                ),
            ],
            options={
                "verbose_name": "Incompatibilidad PAS",
                "verbose_name_plural": "Incompatibilidades PAS",
                "ordering": ["-fecha_deteccion", "persona_id"],
            },
        ),
        migrations.AddConstraint(
            model_name="pascontrolrenaper",
            constraint=models.UniqueConstraint(
                fields=("persona", "fecha_consulta"),
                name="pas_renaper_persona_fecha_uniq",
            ),
        ),
        migrations.AddConstraint(
            model_name="pasincompatibilidad",
            constraint=models.UniqueConstraint(
                fields=("persona", "categoria", "periodo_impacto"),
                name="pas_incompat_persona_categoria_periodo_uniq",
            ),
        ),
    ]
