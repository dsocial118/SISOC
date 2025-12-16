# Generated manually for ETAPA 3

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('ciudadanos', '0017_programatransferencia'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistorialTransferencia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mes', models.IntegerField()),
                ('anio', models.IntegerField()),
                ('monto_auh', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('monto_prestacion_alimentar', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('monto_centro_familia', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('monto_comedor', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('creado', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('modificado', models.DateTimeField(auto_now=True)),
                ('ciudadano', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='historial_transferencias', to='ciudadanos.ciudadano')),
            ],
            options={
                'verbose_name': 'Historial de Transferencia',
                'verbose_name_plural': 'Historial de Transferencias',
                'ordering': ['-anio', '-mes'],
            },
        ),
        migrations.AddConstraint(
            model_name='historialtransferencia',
            constraint=models.UniqueConstraint(fields=('ciudadano', 'mes', 'anio'), name='unique_historial_ciudadano_mes_anio'),
        ),
    ]
