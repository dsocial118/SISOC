from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("comedores", "0059_comedorpwacreateoperation")]

    operations = [
        migrations.AddField(
            model_name="prestacionalimentariaconformidad",
            name="dni_certificador",
            field=models.CharField(blank=True, max_length=8, null=True),
        ),
    ]
