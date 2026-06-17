from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pwa", "0018_catalogoactividadpwa_manage_permission"),
    ]

    operations = [
        migrations.AddField(
            model_name="actividadespaciopwa",
            name="responsable_actividad",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="actividadespaciopwa",
            name="vigencia_actividad_meses",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
    ]
