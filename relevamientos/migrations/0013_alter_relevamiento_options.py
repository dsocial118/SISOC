from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("relevamientos", "0012_relevamiento_territorial_user"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="relevamiento",
            options={
                "permissions": [
                    ("review_relevamiento", "Puede revisar y finalizar relevamientos"),
                ],
                "verbose_name": "Relevamiento",
                "verbose_name_plural": "Relevamientos",
            },
        ),
    ]
