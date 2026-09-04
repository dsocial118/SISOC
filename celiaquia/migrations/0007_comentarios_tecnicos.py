"""Comentarios técnicos estructurados sobre el legajo (issue #2318).

Extiende `HistorialComentarios` en lugar de crear un modelo aparte: el timeline
ya aporta legajo, usuario, fecha, `estado_relacionado` (estado del legajo al
momento del comentario) y `es_interno` (interno hasta que se publica a la
Provincia). Los campos nuevos son todos nulos, así que las filas existentes y
el resto de los tipos de comentario no se ven afectados y no hace falta ninguna
data migration.
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("celiaquia", "0006_seed_permisos_dashboard_reporte"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="historialcomentarios",
            name="observacion_codigo",
            field=models.CharField(
                blank=True,
                help_text="Código de la observación del catálogo ('OTROS' = texto libre)",
                max_length=40,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="historialcomentarios",
            name="publicado_en",
            field=models.DateTimeField(
                blank=True,
                help_text="Fecha en que el comentario dejó de ser interno y se publicó",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="historialcomentarios",
            name="publicado_por",
            field=models.ForeignKey(
                blank=True,
                help_text="Usuario que publicó el comentario a la Provincia",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="comentarios_publicados",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="historialcomentarios",
            name="tiene_observaciones",
            field=models.BooleanField(
                blank=True,
                help_text="Sí/No de la revisión. Solo las que son Sí se publican a Provincia",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="historialcomentarios",
            name="tipo_documento",
            field=models.CharField(
                blank=True,
                choices=[
                    ("RENAPER", "RENAPER"),
                    ("ANSES", "ANSES"),
                    ("CONDICION_DIAGNOSTICA", "Condición diagnóstica"),
                ],
                help_text="Tipo de documento revisado (solo en comentarios técnicos)",
                max_length=30,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="historialcomentarios",
            name="tipo_comentario",
            field=models.CharField(
                choices=[
                    ("VALIDACION_TECNICA", "Validación Técnica"),
                    ("SUBSANACION_MOTIVO", "Motivo de Subsanación"),
                    ("SUBSANACION_RESPUESTA", "Respuesta de Subsanación"),
                    ("RENAPER_VALIDACION", "Validación RENAPER"),
                    ("OBSERVACION_GENERAL", "Observación General"),
                    ("CRUCE_SINTYS", "Cruce SINTYS"),
                    ("PAGO_OBSERVACION", "Observación de Pago"),
                    ("COMENTARIO_TECNICO", "Comentario Técnico"),
                ],
                db_index=True,
                max_length=30,
            ),
        ),
        migrations.AddIndex(
            model_name="historialcomentarios",
            index=models.Index(
                fields=["legajo", "tipo_comentario", "tiene_observaciones"],
                name="hist_com_leg_tipo_obs_idx",
            ),
        ),
    ]
