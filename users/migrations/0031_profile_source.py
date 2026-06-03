from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0030_profile_territorial_scope"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="source",
            field=models.CharField(
                blank=True,
                default="sisoc",
                help_text=(
                    "Sistema que originó el usuario (sisoc, ticketera, ...). "
                    "Permite reconciliar altas provenientes de integraciones externas."
                ),
                max_length=50,
                verbose_name="Origen del usuario",
            ),
        ),
    ]
