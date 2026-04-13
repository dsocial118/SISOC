from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("VAT", "0037_planversioncurricular_provincia_activo_idx"),
    ]

    operations = [
        migrations.AddField(
            model_name="curso",
            name="prioritario",
            field=models.BooleanField(
                db_index=True,
                default=False,
                help_text="Marca si el curso debe destacarse como prioritario en las consultas operativas.",
                verbose_name="Prioritario",
            ),
        ),
    ]