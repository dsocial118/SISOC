# Generated manually for ETAPA 1

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ciudadanos', '0015_cleanup_ciudadano_legacy_columns'),
    ]

    operations = [
        migrations.AddField(
            model_name='ciudadano',
            name='latitud',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='ciudadano',
            name='longitud',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='ciudadano',
            name='estado_civil',
            field=models.CharField(blank=True, choices=[('soltero', 'Soltero/a'), ('casado', 'Casado/a'), ('divorciado', 'Divorciado/a'), ('viudo', 'Viudo/a'), ('union_convivencial', 'Unión convivencial')], max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='ciudadano',
            name='cuil_cuit',
            field=models.CharField(blank=True, max_length=13, null=True),
        ),
        migrations.AddField(
            model_name='ciudadano',
            name='origen_dato',
            field=models.CharField(choices=[('anses', 'ANSES'), ('renaper', 'RENAPER'), ('manual', 'Carga Manual'), ('migracion', 'Migración')], default='manual', max_length=20),
        ),
    ]
