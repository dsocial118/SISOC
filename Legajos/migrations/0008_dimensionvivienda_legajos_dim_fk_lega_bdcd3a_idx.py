# Generated by Django 4.0.2 on 2024-07-10 20:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Legajos', '0007_dimensioneducacion_legajos_dim_fk_lega_bc4d41_idx'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='dimensionvivienda',
            index=models.Index(fields=['fk_legajo'], name='Legajos_dim_fk_lega_bdcd3a_idx'),
        ),
    ]