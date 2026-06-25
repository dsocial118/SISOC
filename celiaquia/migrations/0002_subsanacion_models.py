import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


TIPOS_VALIDOS = {"DOCUMENTACION", "DATOS_PERSONALES", "RENAPER", "OTROS"}


def crear_subsanaciones_desde_legacy(apps, schema_editor):
    """Convierte cada legajo en estado SUBSANAR (modelo viejo de un solo tipo +
    motivo) en una Subsanacion con una observación, preservando el motivo, el
    tipo, el usuario solicitante y la fecha de solicitud."""
    ExpedienteCiudadano = apps.get_model("celiaquia", "ExpedienteCiudadano")
    Subsanacion = apps.get_model("celiaquia", "Subsanacion")
    SubsanacionObservacion = apps.get_model("celiaquia", "SubsanacionObservacion")

    legajos = ExpedienteCiudadano.objects.filter(revision_tecnico="SUBSANAR")
    for legajo in legajos.iterator():
        if legajo.subsanaciones.exists():
            continue

        subsanacion = Subsanacion.objects.create(
            legajo=legajo,
            estado="PENDIENTE",
            motivo_general=legajo.subsanacion_motivo or "",
            solicitada_por=legajo.subsanacion_usuario,
        )
        # solicitada_en es auto_now_add: se preserva la fecha original via update.
        if legajo.subsanacion_solicitada_en:
            Subsanacion.objects.filter(pk=subsanacion.pk).update(
                solicitada_en=legajo.subsanacion_solicitada_en
            )

        tipo = (legajo.subsanacion_tipo or "OTROS").strip().upper()
        if tipo not in TIPOS_VALIDOS:
            tipo = "OTROS"
        SubsanacionObservacion.objects.create(
            subsanacion=subsanacion,
            tipo=tipo,
            detalle=legajo.subsanacion_motivo or "",
        )


class Migration(migrations.Migration):

    dependencies = [
        ("celiaquia", "0001_squashed_0012"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Subsanacion",
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
                    "estado",
                    models.CharField(
                        choices=[
                            ("PENDIENTE", "Pendiente de respuesta"),
                            ("RESPONDIDA", "Respondida por la provincia"),
                        ],
                        db_index=True,
                        default="PENDIENTE",
                        max_length=12,
                    ),
                ),
                (
                    "motivo_general",
                    models.TextField(
                        blank=True,
                        help_text="Motivo general/observación libre",
                        null=True,
                    ),
                ),
                ("solicitada_en", models.DateTimeField(auto_now_add=True)),
                ("respondida_en", models.DateTimeField(blank=True, null=True)),
                (
                    "legajo",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="subsanaciones",
                        to="celiaquia.expedienteciudadano",
                    ),
                ),
                (
                    "solicitada_por",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="subsanaciones_solicitadas",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "respondida_por",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="subsanaciones_v2_respondidas",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Subsanación",
                "verbose_name_plural": "Subsanaciones",
                "ordering": ("-solicitada_en", "pk"),
            },
        ),
        migrations.CreateModel(
            name="SubsanacionObservacion",
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
                    "tipo",
                    models.CharField(
                        choices=[
                            ("DOCUMENTACION", "Documentación"),
                            ("DATOS_PERSONALES", "Datos personales"),
                            ("RENAPER", "RENAPER"),
                            ("OTROS", "Otros"),
                        ],
                        max_length=20,
                    ),
                ),
                ("detalle", models.TextField(blank=True, null=True)),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                (
                    "subsanacion",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="observaciones",
                        to="celiaquia.subsanacion",
                    ),
                ),
            ],
            options={
                "verbose_name": "Observación de Subsanación",
                "verbose_name_plural": "Observaciones de Subsanación",
                "ordering": ("pk",),
            },
        ),
        migrations.CreateModel(
            name="SubsanacionArchivo",
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
                    models.FileField(upload_to="legajos/subsanaciones/"),
                ),
                ("descripcion", models.CharField(blank=True, max_length=255)),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                (
                    "subsanacion",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="archivos",
                        to="celiaquia.subsanacion",
                    ),
                ),
                (
                    "observacion",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="archivos",
                        to="celiaquia.subsanacionobservacion",
                    ),
                ),
                (
                    "usuario",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="subsanacion_archivos_subidos",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Archivo de Subsanación",
                "verbose_name_plural": "Archivos de Subsanación",
                "ordering": ("-creado_en", "pk"),
            },
        ),
        migrations.AddIndex(
            model_name="subsanacion",
            index=models.Index(
                fields=["legajo", "-solicitada_en"], name="subs_legajo_fecha_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="subsanacionobservacion",
            index=models.Index(fields=["subsanacion"], name="subs_obs_subs_idx"),
        ),
        migrations.AddIndex(
            model_name="subsanacionarchivo",
            index=models.Index(
                fields=["subsanacion", "-creado_en"], name="subs_arch_subs_fecha_idx"
            ),
        ),
        migrations.RunPython(
            crear_subsanaciones_desde_legacy,
            migrations.RunPython.noop,
        ),
    ]
