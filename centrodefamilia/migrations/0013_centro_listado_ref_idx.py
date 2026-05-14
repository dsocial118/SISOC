from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("centrodefamilia", "0012_alter_actividad_managers_and_more"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="centro",
            index=models.Index(
                fields=["referente", "id"],
                name="cdf_centro_ref_id_idx",
            ),
        ),
    ]
