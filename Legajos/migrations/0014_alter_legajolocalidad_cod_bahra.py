# Generated by Django 4.0.2 on 2024-08-16 17:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Legajos', '0013_alter_legajolocalidad_nombre_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='legajolocalidad',
            name='cod_bahra',
            field=models.BigIntegerField(),
        ),
    ]
