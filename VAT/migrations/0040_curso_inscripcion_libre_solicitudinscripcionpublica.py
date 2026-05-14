from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("VAT", "0039_comision_lista_espera"),
    ]

    operations = [
        migrations.AddField(
            model_name="curso",
            name="inscripcion_libre",
            field=models.BooleanField(
                default=False,
                help_text=(
                    "Si está activo, el curso admite solicitudes públicas sin ciudadano "
                    "previo y SISOC debe vincularlas antes de convertirlas en inscripción."
                ),
                verbose_name="Inscripción libre",
            ),
        ),
        migrations.CreateModel(
            name="SolicitudInscripcionPublica",
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
                    "deleted_at",
                    models.DateTimeField(blank=True, db_index=True, null=True),
                ),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("pendiente", "Pendiente"),
                            ("vinculada", "Vinculada"),
                            ("convertida", "Convertida"),
                            ("rechazada", "Rechazada"),
                        ],
                        default="pendiente",
                        max_length=20,
                        verbose_name="Estado",
                    ),
                ),
                (
                    "origen_canal",
                    models.CharField(
                        choices=[
                            ("front_publico", "Front Público"),
                            ("backoffice", "Backoffice"),
                            ("api", "API"),
                            ("importacion", "Importación"),
                        ],
                        default="front_publico",
                        max_length=30,
                        verbose_name="Origen del Canal",
                    ),
                ),
                (
                    "datos_postulante",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        verbose_name="Datos del postulante",
                    ),
                ),
                (
                    "observaciones",
                    models.TextField(
                        blank=True, null=True, verbose_name="Observaciones"
                    ),
                ),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
                ("fecha_modificacion", models.DateTimeField(auto_now=True)),
                (
                    "ciudadano",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="solicitudes_publicas_vat",
                        to="ciudadanos.ciudadano",
                        verbose_name="Ciudadano",
                    ),
                ),
                (
                    "comision_curso",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="solicitudes_publicas",
                        to="VAT.comisioncurso",
                        verbose_name="Comisión de Curso",
                    ),
                ),
                (
                    "deleted_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "inscripcion",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="solicitudes_publicas",
                        to="VAT.inscripcion",
                        verbose_name="Inscripción vinculada",
                    ),
                ),
                (
                    "programa",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="solicitudes_publicas_vat",
                        to="core.programa",
                        verbose_name="Programa",
                    ),
                ),
            ],
            options={
                "verbose_name": "Solicitud pública de inscripción",
                "verbose_name_plural": "Solicitudes públicas de inscripción",
                "ordering": ["-fecha_creacion"],
            },
        ),
        migrations.AddIndex(
            model_name="solicitudinscripcionpublica",
            index=models.Index(
                fields=["comision_curso", "estado"],
                name="vat_sol_pub_com_est_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="solicitudinscripcionpublica",
            index=models.Index(
                fields=["ciudadano", "estado"],
                name="vat_sol_pub_ciu_est_idx",
            ),
        ),
    ]
