from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0017_accesocomedorpwa_tipo_asociacion_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="temporary_password_plaintext",
            field=models.CharField(
                blank=True,
                help_text=(
                    "Se muestra en el detalle del usuario hasta que la persona "
                    "cambie su contraseña por primera vez."
                ),
                max_length=255,
                null=True,
                verbose_name="Contraseña temporal visible",
            ),
        ),
    ]
