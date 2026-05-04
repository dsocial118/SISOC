from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("comedores", "0036_capacitacion_comedor_certificado"),
    ]

    operations = [
        migrations.AddField(
            model_name="imagencomedor",
            name="origen",
            field=models.CharField(
                choices=[("web", "Web"), ("mobile", "Mobile")],
                default="web",
                max_length=10,
            ),
        ),
    ]
