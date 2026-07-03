# Generated manually in FAST mode.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admisiones", "0067_repair_informetecnicopdf_missing_columns"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="admision",
            constraint=models.UniqueConstraint(
                fields=("comedor",),
                condition=models.Q(vigente_pwa=True),
                name="uniq_admision_vigente_pwa_por_comedor",
            ),
        ),
    ]
