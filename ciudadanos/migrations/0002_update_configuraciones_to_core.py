from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("ciudadanos", "0001_initial"),
        ("core", "0002_move_configuraciones_data"),  # Asegurar que los datos ya fueron movidos
    ]

    operations = [
        # Actualizar ForeignKey en modelo Ciudadano
        migrations.AlterField(
            model_name='ciudadano',
            name='localidad',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.localidad'),
        ),
        migrations.AlterField(
            model_name='ciudadano',
            name='municipio',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.municipio'),
        ),
        migrations.AlterField(
            model_name='ciudadano',
            name='provincia',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.provincia'),
        ),
        migrations.AlterField(
            model_name='ciudadano',
            name='sexo',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.sexo'),
        ),
        
        # Actualizar ForeignKey en modelo DimensionEducacion
        migrations.AlterField(
            model_name='dimensioneducacion',
            name='localidadInstitucion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='localidadInstitucion', to='core.localidad'),
        ),
        migrations.AlterField(
            model_name='dimensioneducacion',
            name='municipioInstitucion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='municipioInstitucion', to='core.municipio'),
        ),
        migrations.AlterField(
            model_name='dimensioneducacion',
            name='provinciaInstitucion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='provinciaInstitucion', to='core.provincia'),
        ),
        
        # Actualizar ForeignKey en modelo Organismo
        migrations.AlterField(
            model_name='organismo',
            name='localidad',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.localidad'),
        ),
    ]