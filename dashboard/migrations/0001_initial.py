# Generated by Django 4.0.2 on 2024-08-16 17:07

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Dashboard",
            fields=[
                (
                    "llave",
                    models.CharField(
                        help_text="Llave única para identificar el registro en el dashboard.",
                        max_length=250,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                (
                    "cantidad",
                    models.BigIntegerField(
                        default=0,
                        help_text="Cantidad asociada al registro en el dashboard.",
                    ),
                ),
            ],
        ),
    ]