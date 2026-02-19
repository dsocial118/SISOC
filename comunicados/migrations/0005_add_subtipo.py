from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("comunicados", "0004_create_v2_groups"),
    ]

    operations = [
        migrations.AddField(
            model_name="comunicado",
            name="subtipo",
            field=models.CharField(
                blank=True,
                choices=[
                    ("institucional", "Comunicación Institucional"),
                    ("comedores", "Comunicación a Comedores"),
                ],
                default="",
                max_length=20,
                verbose_name="Subtipo de comunicado",
            ),
        ),
    ]
