# pylint: disable=invalid-name

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("VAT", "0045_centro_referentes_revisores"),
    ]

    operations = [
        migrations.AddField(
            model_name="curso",
            name="tipo",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="Tipos seleccionados para el curso (por ejemplo: presencial, virtual o mixto).",
                verbose_name="Tipo",
            ),
        ),
    ]
