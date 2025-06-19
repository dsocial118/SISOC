from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("cdi", "0001_initial"),
    ]

    operations = [
        # Actualizar ForeignKey en modelo CentroDesarrolloInfantil
        migrations.AlterField(
            model_name='centrodesarrolloinfantil',
            name='localidad',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.localidad'),
        ),
        migrations.AlterField(
            model_name='centrodesarrolloinfantil',
            name='municipio',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.municipio'),
        ),
        migrations.AlterField(
            model_name='centrodesarrolloinfantil',
            name='provincia',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.provincia'),
        ),
        
        # Actualizar ManyToMany fields
        migrations.AlterField(
            model_name='centrodesarrolloinfantil',
            name='dias_funcionamiento',
            field=models.ManyToManyField(blank=True, to='core.dia'),
        ),
        migrations.AlterField(
            model_name='centrodesarrolloinfantil',
            name='meses_funcionamiento',
            field=models.ManyToManyField(blank=True, to='core.mes'),
        ),
        migrations.AlterField(
            model_name='centrodesarrolloinfantil',
            name='turnos_funcionamiento',
            field=models.ManyToManyField(blank=True, to='core.turno'),
        ),
    ]