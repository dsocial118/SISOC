from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "centrodefamilia",
            "0008_padronbeneficiarios_beneficiariosresponsablesrenaper_and_more",
        ),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="beneficiariosresponsablesrenaper",
            constraint=models.UniqueConstraint(
                fields=("dni", "genero", "tipo"), name="unique_dni_genero_tipo"
            ),
        ),
    ]
