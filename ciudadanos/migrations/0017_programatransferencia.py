# Generated manually for ETAPA 2

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('ciudadanos', '0016_add_ciudadano_etapa1_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProgramaTransferencia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('auh', 'AUH'), ('prestacion_alimentar', 'Prestación Alimentar'), ('centro_familia', 'Centro de Familia'), ('comedor', 'Asiste a comedor'), ('aduana', 'Aduana')], max_length=30)),
                ('categoria', models.CharField(choices=[('directa', 'Transferencia Directa'), ('indirecta', 'Transferencia Indirecta')], max_length=20)),
                ('monto', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('cantidad_texto', models.CharField(blank=True, help_text="Ej: '2 colchones'", max_length=100, null=True)),
                ('activo', models.BooleanField(default=True)),
                ('creado', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('modificado', models.DateTimeField(auto_now=True)),
                ('ciudadano', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='programas_transferencia', to='ciudadanos.ciudadano')),
            ],
            options={
                'verbose_name': 'Programa de Transferencia',
                'verbose_name_plural': 'Programas de Transferencia',
                'ordering': ['categoria', 'tipo'],
            },
        ),
    ]
