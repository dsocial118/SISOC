from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("encuestas", "0002_opcionpregunta_puntaje_pregunta_pondera_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="encuesta",
            name="es_opcional",
            field=models.BooleanField(
                default=False, verbose_name="¿Se puede descartar?"
            ),
        ),
        migrations.AddField(
            model_name="recordatoriousuario",
            name="descartada",
            field=models.BooleanField(default=False, verbose_name="Ronda descartada"),
        ),
        migrations.AlterField(
            model_name="encuesta",
            name="intervalo_recordatorio_dias",
            field=models.PositiveIntegerField(
                null=True,
                blank=True,
                verbose_name="Intervalo de recordatorio (días)",
                help_text="Solo aplica si la encuesta es postergable.",
            ),
        ),
    ]
