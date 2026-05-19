from django.conf import settings
import core.soft_delete
from django.db import migrations, models
import django.db.models.deletion


DOCUMENTOS = {
    "personeria_juridica": [
        ("Acta Constitutiva de la organizacion", True),
        ("Estatuto social vigente", True),
        ("Resolucion de otorgamiento de la Personeria Juridica", True),
        ("Acta de designacion de autoridades vigentes", True),
        ("DNI del Presidente", True),
        ("DNI del Tesorero", True),
        ("DNI del Secretario", True),
        ("Acta de solicitud de subsidio al programa", True),
        ("Constancia de inscripcion ante ARCA", True),
        ("Constancia de preinscripcion en ReNaCOM", False),
        ("Constancia de validacion en ReNaCOM", False),
        ("Constancia de inscripcion definitiva en ReNaCOM", False),
    ],
    "personeria_eclesiastica": [
        ("Acta o documento de designacion de la Autoridad Maxima", True),
        ("Certificado de culto vigente", True),
        ("DNI del Obispo o autoridad eclesiastica", True),
        ("Constancia de inscripcion ante ARCA", True),
        ("Constancia de preinscripcion en ReNaCOM", False),
        ("Constancia de validacion en ReNaCOM", False),
        ("Constancia de inscripcion definitiva en ReNaCOM", False),
        ("Decreto de reconocimiento del Estado Nacional", False),
        ("Documento de designacion de apoderado", False),
        ("DNI del apoderado", False),
        ("Estatuto institucional", False),
        ("Acta de conformacion de la comision diocesana", False),
        ("Autorizacion para gestionar", False),
    ],
    "organizacion_base": [
        ("Acta de asamblea constitutiva", True),
        ("DNI del Responsable 1", True),
        ("DNI del Responsable 2", True),
        (
            "Acta Designacion Aval 1 - Designacion de cargo Aval 1 "
            "(persona fisica o juridica)",
            True,
        ),
        (
            "DNI de la Autoridad Maxima del Aval 1 / DNI del Aval 1 "
            "(segun corresponda)",
            True,
        ),
        (
            "Acta Designacion Aval 2 - Designacion de cargo Aval 2 "
            "(persona fisica o juridica)",
            True,
        ),
        (
            "DNI de la Autoridad Maxima del Aval 2 / DNI del Aval 2 "
            "(segun corresponda)",
            True,
        ),
        ("Nota de aval emitida por el Aval 1", True),
        ("Nota de aval emitida por el Aval 2", True),
        ("Acta constitutiva del Aval 1", False),
        ("Estatuto del Aval 1", False),
        ("Resolucion de Personeria Juridica del Aval 1", False),
        ("Acta constitutiva del Aval 2", False),
        ("Estatuto del Aval 2", False),
        ("Resolucion de Personeria Juridica del Aval 2", False),
        ("Constancia de preinscripcion en ReNaCOM", False),
        ("Constancia de validacion en ReNaCOM", False),
        ("Constancia de inscripcion definitiva en ReNaCOM", False),
    ],
}


def cargar_documentaciones(apps, schema_editor):
    DocumentacionOrganizacion = apps.get_model(
        "organizaciones", "DocumentacionOrganizacion"
    )
    for categoria, documentos in DOCUMENTOS.items():
        for orden, (nombre, obligatorio) in enumerate(documentos, start=1):
            DocumentacionOrganizacion.objects.update_or_create(
                categoria=categoria,
                nombre=nombre,
                defaults={"obligatorio": obligatorio, "orden": orden},
            )


def borrar_documentaciones(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("organizaciones", "0011_remove_organizacion_cuit_unique"),
    ]

    operations = [
        migrations.CreateModel(
            name="DocumentacionOrganizacion",
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
                ("nombre", models.CharField(max_length=255)),
                (
                    "categoria",
                    models.CharField(
                        choices=[
                            (
                                "personeria_juridica",
                                "Organizacion con personeria juridica",
                            ),
                            (
                                "personeria_eclesiastica",
                                "Personeria juridica eclesiastica",
                            ),
                            ("organizacion_base", "Organizacion de base"),
                        ],
                        max_length=40,
                    ),
                ),
                ("obligatorio", models.BooleanField(default=True)),
                ("orden", models.PositiveIntegerField(default=0)),
            ],
            options={
                "verbose_name": "Documentacion de organizacion",
                "verbose_name_plural": "Documentaciones de organizacion",
                "ordering": ["categoria", "orden", "id"],
            },
        ),
        migrations.CreateModel(
            name="ArchivoOrganizacion",
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
                ("deleted_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                (
                    "archivo",
                    models.FileField(upload_to="organizaciones/documentacion/"),
                ),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("pendiente", "Pendiente"),
                            ("Documento adjunto", "Documento adjunto"),
                            ("A Validar Abogado", "A Validar Abogado"),
                            ("Rectificar", "Rectificar"),
                            ("Aceptado", "Aceptado"),
                        ],
                        default="Documento adjunto",
                        max_length=20,
                    ),
                ),
                ("fecha_vencimiento", models.DateField(blank=True, null=True)),
                ("observaciones", models.TextField(blank=True, null=True)),
                ("creado", models.DateTimeField(auto_now_add=True)),
                ("modificado", models.DateTimeField(auto_now=True)),
                (
                    "creado_por",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="organizaciones_archivos_creados",
                        to=settings.AUTH_USER_MODEL,
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
                    "documentacion",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="archivos",
                        to="organizaciones.documentacionorganizacion",
                    ),
                ),
                (
                    "modificado_por",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="organizaciones_archivos_modificados",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "organizacion",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="archivos_documentacion",
                        to="organizaciones.organizacion",
                    ),
                ),
            ],
            options={
                "verbose_name": "Archivo de organizacion",
                "verbose_name_plural": "Archivos de organizacion",
                "ordering": ["-creado", "-id"],
            },
            managers=[
                ("objects", core.soft_delete.SoftDeleteManager()),
                (
                    "all_objects",
                    core.soft_delete.SoftDeleteManager(include_deleted=True),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="archivoorganizacion",
            index=models.Index(
                fields=["organizacion", "documentacion", "-creado"],
                name="org_doc_archivo_idx",
            ),
        ),
        migrations.RunPython(cargar_documentaciones, borrar_documentaciones),
    ]
