# Generated manually

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('comedores', '0012_alter_comedor_estado_general'),
    ]

    operations = [
        migrations.AddField(
            model_name='comedor',
            name='estado_validacion',
            field=models.CharField(choices=[('Pendiente', 'Pendiente'), ('Validado', 'Validado'), ('No Validado', 'No Validado')], default='Pendiente', max_length=20, verbose_name='Estado de validación'),
        ),
        migrations.AddField(
            model_name='comedor',
            name='fecha_validado',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Fecha de validación'),
        ),
        migrations.CreateModel(
            name='HistorialValidacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado_validacion', models.CharField(choices=[('Pendiente', 'Pendiente'), ('Validado', 'Validado'), ('No Validado', 'No Validado')], max_length=20)),
                ('comentario', models.TextField(verbose_name='Comentario')),
                ('fecha_validacion', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de validación')),
                ('comedor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='historial_validaciones', to='comedores.comedor')),
                ('usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Historial de validación',
                'verbose_name_plural': 'Historiales de validación',
                'ordering': ['-fecha_validacion'],
            },
        ),
        migrations.AddIndex(
            model_name='historialvalidacion',
            index=models.Index(fields=['comedor', 'fecha_validacion'], name='comedores_h_comedor_b8b8c8_idx'),
        ),
    ]