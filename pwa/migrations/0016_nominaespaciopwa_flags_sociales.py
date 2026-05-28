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
        migrations.AddIndex(
            model_name="nominaespaciopwa",
            index=models.Index(
                fields=["pertenece_comunidad_indigena"],
                name="pwa_nomina_indig_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="nominaespaciopwa",
            index=models.Index(fields=["situacion_calle"], name="pwa_nomina_calle_idx"),
        ),
    ]
