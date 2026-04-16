# Migración Fase 1 — Modelo de identidad en Ciudadano
#
# Qué hace:
#   1. Agrega los campos de identidad (tipo_registro_identidad, estado_validacion_renaper,
#      motivo_sin_dni, motivo_no_validacion_renaper, requiere_revision_manual,
#      identificador_interno, documento_unico_key, fecha_validacion_renaper, datos_renaper).
#   2. Sincroniza el estado Django de unique_together (nunca existió en la DB real —
#      confirmado con SHOW INDEX en 2026-04-10: no hay índice único sobre
#      (tipo_documento, documento), lo que explica los 24.926 duplicados en producción).
#
# Qué NO hace:
#   - No backfill de datos. El backfill se hace con el comando de management
#     `backfill_identidad` por separado, después de auditar duplicados.
#
# atomic = False porque MySQL no soporta DDL transaccional. En caso de falla
# parcial, los campos quedaron agregados pero sin datos — el backfill es idempotente.
#
# Ver: docs/registro/decisiones/2026-04-10-identidad-ciudadano.md

from django.db import migrations, models


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("ciudadanos", "0022_alter_ciudadano_managers_and_more"),
    ]

    operations = [
        # 1. Sincronizar unique_together en el estado Django sin tocar la DB.
        #    SHOW INDEX (2026-04-10) confirmó que el índice único sobre
        #    (tipo_documento, documento) NUNCA existió en MySQL — solo estaba
        #    declarado en el modelo. AlterUniqueTogether fallaría buscando un
        #    constraint que no existe, por eso usamos SeparateDatabaseAndState:
        #    actualiza el estado Django sin emitir DDL.
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterUniqueTogether(
                    name="ciudadano",
                    unique_together=set(),
                ),
            ],
        ),
        # 2. Campos de clasificación de identidad
        migrations.AddField(
            model_name="ciudadano",
            name="tipo_registro_identidad",
            field=models.CharField(
                max_length=30,
                choices=[
                    ("ESTANDAR", "Estándar"),
                    ("SIN_DNI", "Sin DNI"),
                    ("DNI_NO_VALIDADO_RENAPER", "DNI no validado por RENAPER"),
                ],
                default="ESTANDAR",
                db_index=True,
            ),
        ),
        migrations.AddField(
            model_name="ciudadano",
            name="estado_validacion_renaper",
            field=models.CharField(
                max_length=20,
                choices=[
                    ("NO_CONSULTADO", "No consultado"),
                    ("VALIDADO", "Validado"),
                    ("NO_VALIDADO", "No validado"),
                ],
                default="NO_CONSULTADO",
                db_index=True,
            ),
        ),
        migrations.AddField(
            model_name="ciudadano",
            name="fecha_validacion_renaper",
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name="ciudadano",
            name="datos_renaper",
            field=models.JSONField(null=True, blank=True),
        ),
        # 3. Campos de motivo (opcionales, condicionales al tipo de registro)
        migrations.AddField(
            model_name="ciudadano",
            name="motivo_sin_dni",
            field=models.CharField(
                max_length=30,
                choices=[
                    ("NO_REGISTRADO_NACER", "No fue registrado al nacer"),
                    ("MENOR_SIN_DOCUMENTO", "Menor de edad sin documento tramitado"),
                    ("EXTRANJERO_SIN_DNI", "Extranjero sin DNI argentino"),
                    ("DOCUMENTO_EXTRAVIADO", "Documento extraviado o en trámite"),
                    (
                        "VULNERABILIDAD_EXTREMA",
                        "Víctima de violencia / vulnerabilidad extrema",
                    ),
                    ("OTRO", "Otro"),
                ],
                null=True,
                blank=True,
            ),
        ),
        migrations.AddField(
            model_name="ciudadano",
            name="motivo_sin_dni_descripcion",
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name="ciudadano",
            name="motivo_no_validacion_renaper",
            field=models.CharField(
                max_length=30,
                choices=[
                    (
                        "ERROR_TRANSCRIPCION",
                        "Errores en la transcripción de datos manuales",
                    ),
                    (
                        "RENAPER_DESACTUALIZADO",
                        "Cambios recientes en RENAPER aún no reflejados",
                    ),
                    ("DOC_NO_ACTUALIZADA", "Documentación del usuario no actualizada"),
                    (
                        "ERROR_TIPOGRAFICO",
                        "Errores tipográficos en el ingreso de datos",
                    ),
                    (
                        "MULTIPLES_IDENTIDADES",
                        "Personas con múltiples identidades o nombres",
                    ),
                    (
                        "CAMBIO_NOMBRE_LEGAL",
                        "Cambios de nombre legal no registrados en RENAPER",
                    ),
                    (
                        "DIFERENCIA_FORMATO_NOMBRE",
                        "Diferencias en el formato o tipo de nombre",
                    ),
                    (
                        "DISCREPANCIA_FECHA_NACIMIENTO",
                        "Discrepancias en fechas de nacimiento o partidas",
                    ),
                    ("OTRO", "Otro"),
                ],
                null=True,
                blank=True,
            ),
        ),
        migrations.AddField(
            model_name="ciudadano",
            name="motivo_no_validacion_descripcion",
            field=models.TextField(null=True, blank=True),
        ),
        # 4. Control y trazabilidad
        migrations.AddField(
            model_name="ciudadano",
            name="requiere_revision_manual",
            field=models.BooleanField(default=False, db_index=True),
        ),
        # 5. Clave de búsqueda interna (única, generada por backfill)
        #    null=True es intencional: unique + nullable permite múltiples NULLs
        #    en MySQL para ciudadanos sin identificador asignado aún.
        migrations.AddField(
            model_name="ciudadano",
            name="identificador_interno",
            field=models.CharField(
                max_length=50,
                null=True,
                blank=True,
                unique=True,
            ),
        ),
        # 6. Reemplaza unique_together. Solo se completa en ESTANDAR con DNI único.
        #    NULL en SIN_DNI y DNI_NO_VALIDADO_RENAPER.
        #    null=True es intencional: mismo motivo que identificador_interno.
        migrations.AddField(
            model_name="ciudadano",
            name="documento_unico_key",
            field=models.CharField(
                max_length=60,
                null=True,
                blank=True,
                unique=True,
            ),
        ),
    ]
