from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("relevamientos", "0008_actividadesextrasseguimiento_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="primerseguimiento",
            name="gestionar_id",
            field=models.CharField(
                blank=True,
                max_length=64,
                null=True,
            ),
        ),
    ]
