# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admisiones', '0046_alter_informetecnico_montos_decimal'),
    ]

    operations = [
        migrations.AddField(
            model_name='informetecnico',
            name='no_corresponde_fecha_vencimiento',
            field=models.BooleanField(default=False, verbose_name='No corresponde fecha de vencimiento'),
        ),
    ]