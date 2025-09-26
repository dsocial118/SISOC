# Generated migration to add validado_renaper field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('celiaquia', '0003_remove_dni_requirement'),
    ]

    operations = [
        migrations.AddField(
            model_name='expedienteciudadano',
            name='validado_renaper',
            field=models.BooleanField(default=False, db_index=True),
        ),
    ]