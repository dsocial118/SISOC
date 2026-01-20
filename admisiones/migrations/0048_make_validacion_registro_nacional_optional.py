# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admisiones', '0047_informetecnico_no_corresponde_fecha_vencimiento'),
    ]

    operations = [
        migrations.AlterField(
            model_name='informetecnico',
            name='validacion_registro_nacional',
            field=models.CharField(
                verbose_name='Validación Registro Nacional Comedores/Merenderos',
                max_length=255,
                blank=True,
                null=True,
            ),
        ),
    ]
