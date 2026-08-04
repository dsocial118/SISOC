from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("organizaciones", "0019_restaurar_simple_asociacion_tipo"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProyectoOrganizacion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("codigo", models.CharField(max_length=255)),
                ("nombre", models.CharField(blank=True, max_length=255, null=True)),
                ("activo", models.BooleanField(default=True)),
                (
                    "organizacion",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="proyectos",
                        to="organizaciones.organizacion",
                    ),
                ),
            ],
            options={
                "verbose_name": "Proyecto de organización",
                "verbose_name_plural": "Proyectos de organización",
                "ordering": ["codigo"],
            },
        ),
        migrations.AddConstraint(
            model_name="proyectoorganizacion",
            constraint=models.UniqueConstraint(
                fields=("organizacion", "codigo"),
                name="uq_proyecto_organizacion_codigo",
            ),
        ),
    ]
