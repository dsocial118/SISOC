from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("VAT", "0030_alter_centro_referente_cfp_group"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="curso",
            name="programa",
        ),
    ]