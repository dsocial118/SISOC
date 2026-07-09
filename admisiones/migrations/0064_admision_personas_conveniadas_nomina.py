# Generated manually in FAST mode.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admisiones", "0063_admisiondocorgsnapshot_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="admision",
            name="personas_conveniadas_nomina",
            field=models.PositiveIntegerField(
                blank=True,
                help_text="Tope de personas para nomina alimentaria en PWA.",
                null=True,
                verbose_name="Personas conveniadas para nomina",
            ),
        ),
    ]
