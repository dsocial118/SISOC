from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("VAT", "0004_alter_centro_referente"),
    ]

    operations = [
        migrations.DeleteModel(
            name="InformeCabalRegistro",
        ),
        migrations.DeleteModel(
            name="CabalArchivo",
        ),
    ]
