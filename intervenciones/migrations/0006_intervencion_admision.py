import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admisiones", "0001_squashed_0058"),
        ("intervenciones", "0001_squashed_0005"),
    ]

    operations = [
        migrations.AddField(
            model_name="intervencion",
            name="admision",
            field=models.ForeignKey(
                blank=True,
                db_index=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="intervenciones",
                to="admisiones.admision",
                verbose_name="Admisión",
            ),
        ),
    ]
