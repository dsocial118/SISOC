from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("VAT", "0048_remove_comisioncurso_modalidad"),
    ]

    operations = [
        migrations.AddField(
            model_name="comisioncurso",
            name="cupo_lista_espera",
            field=models.PositiveIntegerField(
                blank=True,
                help_text="Cantidad máxima de inscripciones permitidas en espera.",
                null=True,
                verbose_name="Cupo Lista de Espera",
            ),
        ),
    ]