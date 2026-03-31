from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0021_merge_20260330_0757"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="temporary_password_plaintext",
            field=models.CharField(
                blank=True,
                max_length=128,
                null=True,
                verbose_name="Contraseña temporal visible",
            ),
        ),
    ]
