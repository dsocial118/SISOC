# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('celiaquia', '0003_expedienteciudadano_estado_validacion_renaper_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='RegistroErroneo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fila_excel', models.PositiveIntegerField()),
                ('datos_raw', models.JSONField()),
                ('campo_error', models.CharField(blank=True, max_length=100)),
                ('mensaje_error', models.TextField()),
                ('procesado', models.BooleanField(db_index=True, default=False)),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('procesado_en', models.DateTimeField(blank=True, null=True)),
                ('expediente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='registros_erroneos', to='celiaquia.expediente')),
            ],
            options={
                'verbose_name': 'Registro Erróneo',
                'verbose_name_plural': 'Registros Erróneos',
                'ordering': ('fila_excel',),
                'indexes': [
                    models.Index(fields=['expediente', 'procesado'], name='reg_err_exp_proc_idx'),
                ],
            },
        ),
    ]
