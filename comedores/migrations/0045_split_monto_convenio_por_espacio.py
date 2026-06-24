from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("comedores", "0044_nomina_derivacion"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="comedordatosconveniopnud",
            name="monto_total_convenio_por_espacio",
        ),
        migrations.AddField(
            model_name="comedordatosconveniopnud",
            name="monto_convenio_prestaciones_alimentarias",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True),
        ),
        migrations.AddField(
            model_name="comedordatosconveniopnud",
            name="monto_convenio_siph",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True),
        ),
    ]
