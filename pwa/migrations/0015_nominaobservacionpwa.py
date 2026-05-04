from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("comedores", "0037_imagencomedor_origen"),
        ("pwa", "0014_pushsubscriptionpwa_endpoint_hash"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="NominaObservacionPWA",
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
                ("texto", models.TextField()),
                (
                    "fecha_creacion",
                    models.DateTimeField(auto_now_add=True, db_index=True),
                ),
                (
                    "creada_por",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="observaciones_nomina_pwa_creadas",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "nomina",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="observaciones_pwa",
                        to="comedores.nomina",
                    ),
                ),
            ],
            options={
                "verbose_name": "Observación Nómina PWA",
                "verbose_name_plural": "Observaciones Nómina PWA",
                "ordering": ("-fecha_creacion", "-id"),
            },
        ),
        migrations.AddIndex(
            model_name="nominaobservacionpwa",
            index=models.Index(
                fields=["nomina", "fecha_creacion"], name="pwa_nom_obs_idx"
            ),
        ),
    ]
