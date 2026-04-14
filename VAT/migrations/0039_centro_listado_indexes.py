from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("VAT", "0038_curso_prioritario"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="centro",
            index=models.Index(
                fields=["provincia", "id"],
                name="vat_centro_prov_id_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="centro",
            index=models.Index(
                fields=["referente", "id"],
                name="vat_centro_ref_id_idx",
            ),
        ),
    ]
