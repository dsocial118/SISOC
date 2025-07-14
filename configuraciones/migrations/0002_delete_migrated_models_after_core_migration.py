from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
        ("provincias", "0002_alter_personafisica_provincia_and_more"),
        (
            "ciudadanos",
            "0002_alter_ciudadano_localidad_alter_ciudadano_municipio_and_more",
        ),
        ("comedores", "0003_alter_comedor_localidad_alter_comedor_municipio_and_more"),
        ("cdi", "0002_alter_centrodesarrolloinfantil_dias_funcionamiento_and_more"),
        ("configuraciones", "0001_initial"),
    ]

    operations = [
        migrations.DeleteModel(
            name="Dia",
        ),
        migrations.AlterUniqueTogether(
            name="localidad",
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name="localidad",
            name="municipio",
        ),
        migrations.DeleteModel(
            name="Mes",
        ),
        migrations.AlterUniqueTogether(
            name="municipio",
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name="municipio",
            name="provincia",
        ),
        migrations.DeleteModel(
            name="Sexo",
        ),
        migrations.DeleteModel(
            name="Turno",
        ),
        migrations.DeleteModel(
            name="Localidad",
        ),
        migrations.DeleteModel(
            name="Municipio",
        ),
        migrations.DeleteModel(
            name="Provincia",
        ),
    ]
