# Generated manually for ciudadanos importacion masiva.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import ciudadanos.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("ciudadanos", "0029_ciudadano_estado_revision_manual"),
    ]

    operations = [
        migrations.CreateModel(
            name="CiudadanosImportJob",
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
                    "archivo",
                    models.FileField(
                        upload_to=ciudadanos.models.ciudadanos_import_job_upload_to
                    ),
                ),
                ("original_filename", models.CharField(max_length=255)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pendiente"),
                            ("processing", "Procesando"),
                            ("completed", "Completado"),
                            ("completed_with_errors", "Completado con errores"),
                            ("failed", "Fallido"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=30,
                    ),
                ),
                ("total_rows", models.PositiveIntegerField(default=0)),
                ("processed_rows", models.PositiveIntegerField(default=0)),
                ("created_rows", models.PositiveIntegerField(default=0)),
                ("existing_rows", models.PositiveIntegerField(default=0)),
                ("failed_rows", models.PositiveIntegerField(default=0)),
                ("pending_rows", models.PositiveIntegerField(default=0)),
                ("next_row_index", models.PositiveIntegerField(default=0)),
                (
                    "last_successful_row",
                    models.PositiveIntegerField(blank=True, null=True),
                ),
                (
                    "last_successful_documento",
                    models.CharField(blank=True, max_length=32),
                ),
                (
                    "last_attempted_row",
                    models.PositiveIntegerField(blank=True, null=True),
                ),
                (
                    "last_attempted_documento",
                    models.CharField(blank=True, max_length=32),
                ),
                ("last_error_message", models.TextField(blank=True)),
                ("last_error_type", models.CharField(blank=True, max_length=64)),
                ("last_error_at", models.DateTimeField(blank=True, null=True)),
                ("resume_count", models.PositiveIntegerField(default=0)),
                (
                    "requested_at",
                    models.DateTimeField(auto_now_add=True, db_index=True),
                ),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                (
                    "last_activity_at",
                    models.DateTimeField(blank=True, db_index=True, null=True),
                ),
                (
                    "requested_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="ciudadanos_import_jobs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Lote de importacion masiva de ciudadanos",
                "verbose_name_plural": "Lotes de importacion masiva de ciudadanos",
                "ordering": ["-requested_at", "-id"],
                "indexes": [
                    models.Index(
                        fields=["status", "requested_at"],
                        name="ciudadanos__status_8d0a47_idx",
                    ),
                    models.Index(
                        fields=["requested_by", "requested_at"],
                        name="ciudadanos__request_5b2064_idx",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="CiudadanosImportJobRow",
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
                ("fila", models.PositiveIntegerField()),
                ("documento_raw", models.CharField(blank=True, max_length=64)),
                ("dni", models.CharField(blank=True, max_length=16)),
                ("cuil", models.CharField(blank=True, max_length=11)),
                ("sexo", models.CharField(blank=True, max_length=1)),
                ("sexos_intentados", models.CharField(blank=True, max_length=16)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pendiente"),
                            ("created", "Creado"),
                            ("existing", "Existente"),
                            ("failed", "Fallido"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("mensaje", models.TextField(blank=True)),
                ("error_type", models.CharField(blank=True, max_length=64)),
                ("attempts", models.PositiveIntegerField(default=0)),
                (
                    "processed_at",
                    models.DateTimeField(blank=True, db_index=True, null=True),
                ),
                (
                    "ciudadano",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="import_rows",
                        to="ciudadanos.ciudadano",
                    ),
                ),
                (
                    "job",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="rows",
                        to="ciudadanos.ciudadanosimportjob",
                    ),
                ),
            ],
            options={
                "verbose_name": "Resultado de fila de importacion de ciudadanos",
                "verbose_name_plural": "Resultados de filas de importacion de ciudadanos",
                "ordering": ["fila", "id"],
                "indexes": [
                    models.Index(
                        fields=["job", "status"],
                        name="ciudadanos__job_id_2121af_idx",
                    ),
                    models.Index(
                        fields=["job", "processed_at"],
                        name="ciudadanos__job_id_00c794_idx",
                    ),
                    models.Index(
                        fields=["ciudadano"],
                        name="ciudadanos__ciudada_76bc92_idx",
                    ),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("job", "fila"),
                        name="ciudadanos_import_job_row_unique",
                    )
                ],
            },
        ),
    ]
