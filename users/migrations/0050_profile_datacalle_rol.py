# Escrita a mano; verificar con `makemigrations --check` al levantar el stack.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0049_datacalle_relevador_calle"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="datacalle_rol",
            field=models.CharField(
                blank=True,
                choices=[("entrevistador", "Entrevistador")],
                default="",
                help_text="Rol con el que el usuario opera en SISOC - Mobile DataCalle. Obligatorio cuando es_relevador_calle esta activo.",
                max_length=20,
                verbose_name="Rol en DataCalle",
            ),
        ),
    ]
