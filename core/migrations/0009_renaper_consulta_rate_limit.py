from django.db import migrations, models
from django.utils import timezone


def crear_turno_inicial(apps, schema_editor):
    rate_limit = apps.get_model("core", "RenaperConsultaRateLimit")
    rate_limit.objects.using(schema_editor.connection.alias).create(
        id=1, next_available_at=timezone.now()
    )


class Migration(migrations.Migration):
    dependencies = [("core", "0008_programa_organismo_programa_descripcion")]

    operations = [
        migrations.CreateModel(
            name="RenaperConsultaRateLimit",
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
                ("next_available_at", models.DateTimeField()),
            ],
            options={"verbose_name": "Límite global de consultas RENAPER"},
        ),
        migrations.RunPython(crear_turno_inicial, migrations.RunPython.noop),
    ]
