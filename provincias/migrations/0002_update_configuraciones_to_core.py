from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("provincias", "0001_initial"),
        ("core", "0002_move_configuraciones_data"),
    ]

    operations = [
        # Actualizar ForeignKey en modelo PersonaFisica
        migrations.AlterField(
            model_name='personafisica',
            name='provincia',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.provincia'),
        ),
        
        # Actualizar ForeignKey en modelo PersonaJuridica
        migrations.AlterField(
            model_name='personajuridica',
            name='provincia',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.provincia'),
        ),
        
        # Actualizar ForeignKey en modelo Proyecto
        migrations.AlterField(
            model_name='proyecto',
            name='provincia',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.provincia'),
        ),
    ]