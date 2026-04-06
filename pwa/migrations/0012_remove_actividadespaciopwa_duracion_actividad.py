from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("pwa", "0011_actividadespaciopwa_hora_inicio_hora_fin"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="actividadespaciopwa",
            name="duracion_actividad",
        ),
    ]
