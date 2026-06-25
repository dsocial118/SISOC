from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("celiaquia", "0002_subsanacion_models"),
    ]

    operations = [
        migrations.AddField(
            model_name="historialcomentarios",
            name="es_interno",
            field=models.BooleanField(
                default=False,
                db_index=True,
                help_text="Comentario interno: visible solo para usuarios de Nación",
            ),
        ),
    ]
