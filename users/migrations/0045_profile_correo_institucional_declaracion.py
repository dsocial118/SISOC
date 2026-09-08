from django.db import migrations, models


class Migration(migrations.Migration):
    """Campos pedidos por UX/UI sobre el flujo de confirmación de datos.

    Van en una migración aparte de la 0044 porque esa ya quedó aplicada en
    entornos de desarrollo: editarla no la vuelve a ejecutar.
    """

    dependencies = [
        ("users", "0044_profile_confirmacion_datos"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="correo_institucional",
            field=models.EmailField(
                blank=True,
                max_length=254,
                verbose_name="Correo institucional",
            ),
        ),
        migrations.AddField(
            model_name="profile",
            name="declaracion_aceptada",
            field=models.BooleanField(
                default=False,
                help_text=(
                    "El usuario aceptó la declaración al confirmar sus datos "
                    "personales."
                ),
                verbose_name="Declaración aceptada",
            ),
        ),
    ]
