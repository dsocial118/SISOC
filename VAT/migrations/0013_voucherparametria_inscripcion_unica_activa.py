from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("VAT", "0012_asistenciasesion"),
    ]

    operations = [
        migrations.AddField(
            model_name="voucherparametria",
            name="inscripcion_unica_activa",
            field=models.BooleanField(
                default=False,
                help_text=(
                    "Si está activado, el ciudadano solo puede tener una inscripción "
                    "activa a la vez en comisiones de este programa. Debe completar o "
                    "abandonar la inscripción actual antes de inscribirse en otra."
                ),
                verbose_name="Inscripción única activa",
            ),
        ),
    ]
