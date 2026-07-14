from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_squashed_0007"),
        ("organizaciones", "0001_squashed_0010"),
    ]

    operations = [
        migrations.AddField(
            model_name="programa",
            name="descripcion",
            field=models.TextField(blank=True, null=True, verbose_name="Descripción"),
        ),
        migrations.AddField(
            model_name="programa",
            name="organismo",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="programas",
                to="organizaciones.organizacion",
                verbose_name="Organismo",
            ),
        ),
    ]
