from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ("configuraciones", "0001_initial"),
    ]

    operations = [
        # Eliminar modelo Localidad (primero por las FK)
        migrations.DeleteModel(
            name='Localidad',
        ),
        # Eliminar modelo Municipio (segundo por las FK)
        migrations.DeleteModel(
            name='Municipio',
        ),
        # Eliminar modelos sin relaciones
        migrations.DeleteModel(
            name='Provincia',
        ),
        migrations.DeleteModel(
            name='Mes',
        ),
        migrations.DeleteModel(
            name='Dia',
        ),
        migrations.DeleteModel(
            name='Turno',
        ),
        migrations.DeleteModel(
            name='Sexo',
        ),
    ]