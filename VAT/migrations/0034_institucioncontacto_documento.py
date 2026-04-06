from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("VAT", "0033_planversioncurricular_nombre"),
    ]

    operations = [
        migrations.AddField(
            model_name="institucioncontacto",
            name="documento",
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]