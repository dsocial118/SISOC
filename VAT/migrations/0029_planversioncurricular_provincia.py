from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0008_programa_organismo_programa_descripcion"),
        ("VAT", "0028_comisionhorario_comision_curso_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="planversioncurricular",
            name="provincia",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="vat_planes_estudio",
                to="core.provincia",
                verbose_name="Provincia",
            ),
        ),
    ]
