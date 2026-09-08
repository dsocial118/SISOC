from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("comedores", "0047_remove_conformidad_periodo_unique"),
    ]

    operations = [
        migrations.AddField(
            model_name="comedor",
            name="mes_ejecucion",
            field=models.IntegerField(
                blank=True,
                null=True,
                validators=[MinValueValidator(-2), MaxValueValidator(6)],
                verbose_name="Mes de ejecución",
            ),
        ),
    ]
