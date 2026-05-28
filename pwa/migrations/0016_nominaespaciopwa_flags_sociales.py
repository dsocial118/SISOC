from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("pwa", "0015_nominaobservacionpwa"),
    ]

    operations = [
        migrations.AddField(
            model_name="nominaespaciopwa",
            name="pertenece_comunidad_indigena",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="nominaespaciopwa",
            name="situacion_calle",
            field=models.BooleanField(default=False),
        ),
    ]
