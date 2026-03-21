from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("VAT", "0007_modalidadinstitucional"),
    ]

    operations = [
        migrations.AddField(
            model_name="centro",
            name="clase_institucion",
            field=models.CharField(
                blank=True, max_length=50, null=True, verbose_name="Clase de Institución"
            ),
        ),
        migrations.AddField(
            model_name="centro",
            name="fecha_alta",
            field=models.DateField(blank=True, null=True, verbose_name="Fecha de Alta"),
        ),
        migrations.AddField(
            model_name="centro",
            name="modalidad_institucional",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="vat_centros",
                to="VAT.modalidadinstitucional",
                verbose_name="Modalidad Institucional",
            ),
        ),
        migrations.AddField(
            model_name="centro",
            name="situacion",
            field=models.CharField(
                blank=True, max_length=50, null=True, verbose_name="Situación"
            ),
        ),
        migrations.AddField(
            model_name="centro",
            name="tipo_gestion",
            field=models.CharField(
                blank=True, max_length=50, null=True, verbose_name="Tipo de Gestión"
            ),
        ),
    ]
