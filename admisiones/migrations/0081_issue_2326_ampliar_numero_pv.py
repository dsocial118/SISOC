# Generated manually in FAST mode.

from django.db import migrations, models


class Migration(migrations.Migration):
    """Amplia los campos de numero de PV y unifica el grafo de migraciones.

    Con repartición y organismo de hasta 50 caracteres, el número de PV armado
    puede llegar a 123 caracteres y no entraba en max_length=100.

    Depende de las dos migraciones 0080 para dejar una sola hoja en el grafo.
    """

    dependencies = [
        ("admisiones", "0080_issue_2326_providencias"),
        ("admisiones", "0080_alter_informetecnico_criterio_seleccionado"),
    ]

    operations = [
        migrations.AlterField(
            model_name="providencia",
            name="numero_pv_primera",
            field=models.CharField(
                blank=True,
                max_length=255,
                null=True,
                verbose_name="Número de PV Primera Providencia",
            ),
        ),
        migrations.AlterField(
            model_name="providencia",
            name="numero_gde_pv",
            field=models.CharField(
                blank=True,
                max_length=255,
                null=True,
                verbose_name="Número de GDE PV",
            ),
        ),
    ]
