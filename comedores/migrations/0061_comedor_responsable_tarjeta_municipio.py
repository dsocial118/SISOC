from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_squashed_0007"),
        ("comedores", "0060_prestacionalimentariaconformidad_dni_certificador"),
    ]

    operations = [
        migrations.AddField(
            model_name="comedor",
            name="responsable_tarjeta_municipio",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="comedores_responsable_tarjeta",
                to="core.municipio",
            ),
        ),
    ]
