from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("comedores", "0001_initial"),
        ("core", "0002_move_configuraciones_data"),
    ]

    operations = [
        # Actualizar ForeignKey en modelo Comedor
        migrations.AlterField(
            model_name='comedor',
            name='localidad',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.localidad'),
        ),
        migrations.AlterField(
            model_name='comedor',
            name='municipio',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.municipio'),
        ),
        migrations.AlterField(
            model_name='comedor',
            name='provincia',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.provincia'),
        ),
        
        # Actualizar ForeignKey en modelo Nomina
        migrations.AlterField(
            model_name='nomina',
            name='sexo',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.sexo'),
        ),
    ]