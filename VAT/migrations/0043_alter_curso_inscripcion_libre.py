from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("VAT", "0042_alter_inscripcion_programa"),
    ]

    operations = [
        migrations.AlterField(
            model_name="curso",
            name="inscripcion_libre",
            field=models.BooleanField(
                default=False,
                help_text=(
                    "Si está activo, el curso admite altas públicas aunque el ciudadano "
                    "no exista todavía en SISOC."
                ),
                verbose_name="Inscripción libre",
            ),
        ),
    ]
