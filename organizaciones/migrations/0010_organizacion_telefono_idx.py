from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("organizaciones", "0009_organizacion_sigla"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="organizacion",
            index=models.Index(
                fields=["telefono"],
                name="org_telefono_idx",
            ),
        ),
    ]
