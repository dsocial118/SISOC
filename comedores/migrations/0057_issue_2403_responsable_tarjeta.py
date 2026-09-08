from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        (
            "comedores",
            "0056_imagencomedor_client_uuid_imagencomedor_relevamiento_and_more",
        )
    ]

    operations = [
        migrations.AddField(
            model_name="comedor",
            name="responsable_tarjeta_nombre",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="comedor",
            name="responsable_tarjeta_mail",
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name="comedor",
            name="responsable_tarjeta_dni",
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name="comedor",
            name="responsable_tarjeta_cuit",
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name="comedor",
            name="responsable_tarjeta_domicilio",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="comedor",
            name="responsable_tarjeta_telefono",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name="comedor",
            name="responsable_tarjeta_localidad",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="comedores_responsable_tarjeta",
                to="core.localidad",
            ),
        ),
        migrations.AddField(
            model_name="comedor",
            name="responsable_tarjeta_provincia",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="comedores_responsable_tarjeta",
                to="core.provincia",
            ),
        ),
    ]
