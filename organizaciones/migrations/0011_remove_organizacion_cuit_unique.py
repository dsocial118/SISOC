from django.db import migrations, models
from django.core.validators import MaxValueValidator, MinValueValidator


class Migration(migrations.Migration):
    dependencies = [
        ("organizaciones", "0010_organizacion_telefono_idx"),
    ]

    operations = [
        migrations.AlterField(
            model_name="organizacion",
            name="cuit",
            field=models.BigIntegerField(
                blank=True,
                db_index=True,
                null=True,
                validators=[MinValueValidator(0), MaxValueValidator(99999999999)],
            ),
        ),
    ]
