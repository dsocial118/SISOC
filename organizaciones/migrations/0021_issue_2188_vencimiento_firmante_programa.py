from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("comedores", "0054_issue_2188_personas_declaradas_siph"),
        ("organizaciones", "0020_proyecto_organizacion"),
    ]

    operations = [
        migrations.AddField(
            model_name="organizacion",
            name="sin_vencimiento",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="organizacion",
            name="fecha_vencimiento",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Fecha de vencimiento"),
        ),
        migrations.AddField(
            model_name="firmante",
            name="programa",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="firmantes_organizacion",
                to="comedores.programas",
            ),
        ),
    ]
