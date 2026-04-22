from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("VAT", "0041_alter_solicitudinscripcionpublica_managers"),
    ]

    operations = [
        migrations.AlterField(
            model_name="inscripcion",
            name="programa",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.PROTECT,
                related_name="inscripciones_vat",
                to="core.programa",
                verbose_name="Programa",
            ),
        ),
    ]
