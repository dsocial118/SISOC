from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("admisiones", "0074_variables_compatibilidad_templates_informe_tecnico")
    ]

    operations = [
        migrations.AlterField(
            model_name="admision",
            name="legales_num_if",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
