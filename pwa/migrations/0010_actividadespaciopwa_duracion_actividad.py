from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pwa", "0009_registroasistencianominapwa"),
    ]

    operations = [
        migrations.AddField(
            model_name="actividadespaciopwa",
            name="duracion_actividad",
            field=models.CharField(blank=True, max_length=60, null=True),
        ),
    ]
