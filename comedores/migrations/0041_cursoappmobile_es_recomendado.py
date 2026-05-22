from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("comedores", "0040_alter_cursoappmobile_managers_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="cursoappmobile",
            name="es_recomendado",
            field=models.BooleanField(default=False),
        ),
    ]
