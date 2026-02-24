from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("centrodeinfancia", "0003_centrodeinfancia_calle_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="ObservacionCentroInfancia",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("is_deleted", models.BooleanField(default=False, editable=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("observador", models.CharField(blank=True, max_length=255)),
                (
                    "fecha_visita",
                    models.DateTimeField(blank=True, default=django.utils.timezone.now),
                ),
                ("observacion", models.TextField()),
                (
                    "centro",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="observaciones",
                        to="centrodeinfancia.centrodeinfancia",
                    ),
                ),
            ],
            options={
                "verbose_name": "Observación Centro de Infancia",
                "verbose_name_plural": "Observaciones Centro de Infancia",
            },
        ),
        migrations.AddIndex(
            model_name="observacioncentroinfancia",
            index=models.Index(
                fields=["centro"],
                name="centrodeinfa_centro__4974e2_idx",
            ),
        ),
    ]