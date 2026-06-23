from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("comedores", "0044_nomina_derivacion"),
        ("pwa", "0020_pwa_operacion_permissions"),
    ]

    operations = [
        migrations.CreateModel(
            name="NominaDestinatariosDocumentoPWA",
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
                (
                    "periodo_referencia",
                    models.DateField(help_text="Primer dia del mes certificado."),
                ),
                ("version", models.PositiveIntegerField(default=1)),
                (
                    "archivo",
                    models.FileField(upload_to="pwa/nomina_destinatarios/"),
                ),
                ("cantidad_destinatarios", models.PositiveIntegerField(default=0)),
                ("fecha_generacion", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                (
                    "comedor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="nomina_destinatarios_documentos_pwa",
                        to="comedores.comedor",
                    ),
                ),
                (
                    "generado_por",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="nomina_destinatarios_pwa_generadas",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Documento Nomina Destinatarios PWA",
                "verbose_name_plural": "Documentos Nomina Destinatarios PWA",
                "ordering": ("-periodo_referencia", "-version", "-fecha_generacion"),
            },
        ),
        migrations.AddConstraint(
            model_name="nominadestinatariosdocumentopwa",
            constraint=models.UniqueConstraint(
                fields=("comedor", "periodo_referencia", "version"),
                name="uniq_pwa_nomina_dest_doc_version",
            ),
        ),
        migrations.AddIndex(
            model_name="nominadestinatariosdocumentopwa",
            index=models.Index(
                fields=["comedor", "periodo_referencia"],
                name="pwa_nom_dest_doc_period_idx",
            ),
        ),
    ]
