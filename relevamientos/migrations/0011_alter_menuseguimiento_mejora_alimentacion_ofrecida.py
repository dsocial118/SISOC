from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("relevamientos", "0010_sincronizado_gestionar"),
    ]

    operations = [
        migrations.AlterField(
            model_name="menuseguimiento",
            name="mejora_alimentacion_ofrecida",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
