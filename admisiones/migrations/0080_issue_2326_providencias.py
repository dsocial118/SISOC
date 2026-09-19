# Generated manually in FAST mode.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


ESTADOS_LEGALES = [
    ("Enviado a Legales", "Enviado a Legales"),
    ("A Rectificar", "A Rectificar"),
    ("Rectificado", "Rectificado"),
    ("Pendiente de Validacion", "Pendiente de Validacion"),
    ("Expediente Agregado", "Expediente Agregado"),
    ("Formulario Convenio Creado", "Formulario Convenio Creado"),
    ("IF Convenio Asignado", "IF Convenio Asignado"),
    (
        "Formulario Primera Providencia Creado",
        "Formulario Primera Providencia Creado",
    ),
    ("IF Primera Providencia Asignado", "IF Primera Providencia Asignado"),
    (
        "Formulario Segunda Providencia Creado",
        "Formulario Segunda Providencia Creado",
    ),
    ("IF Segunda Providencia Asignado", "IF Segunda Providencia Asignado"),
    ("Formulario Disposición Creado", "Formulario Disposición Creado"),
    ("IF Disposición Asignado", "IF Disposición Asignado"),
    ("Juridicos: Validado", "Juridicos: Validado"),
    ("Juridicos: Rechazado", "Juridicos: Rechazado"),
    ("Disposición Firmada", "Disposición Firmada"),
    ("Informe SGA Generado", "Informe SGA Generado"),
    ("Convenio Firmado", "Convenio Firmado"),
    ("Acompañamiento Pendiente", "Acompañamiento Pendiente"),
    ("Archivado", "Archivado"),
    ("Informe Complementario Solicitado", "Informe Complementario Solicitado"),
    ("Informe Complementario Enviado", "Informe Complementario Enviado"),
    ("Informe Complementario: Validado", "Informe Complementario: Validado"),
    ("Finalizado", "Finalizado"),
    ("Descartado", "Descartado"),
    ("Inactivada", "Inactivada"),
]


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("admisiones", "0079_issue_1213_variables_documentales_renovacion"),
    ]

    operations = [
        migrations.AlterField(
            model_name="admision",
            name="estado_legales",
            field=models.CharField(
                blank=True,
                choices=ESTADOS_LEGALES,
                max_length=40,
                null=True,
                verbose_name="Estado",
            ),
        ),
        migrations.AlterField(
            model_name="admision",
            name="dictamen_motivo",
            field=models.CharField(
                blank=True,
                choices=[
                    (
                        "observacion en informe técnico",
                        "Observación en informe técnico",
                    ),
                    (
                        "observacion en proyecto de convenio",
                        "Observación en proyecto de convenio",
                    ),
                    (
                        "observacion en proyecto de disposicion",
                        "Observación en providencia",
                    ),
                ],
                max_length=40,
                null=True,
                verbose_name="Tipo de observación",
            ),
        ),
        migrations.CreateModel(
            name="Providencia",
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
                    "orden",
                    models.CharField(
                        choices=[
                            ("primera", "Primera Providencia"),
                            ("segunda", "Segunda Providencia"),
                        ],
                        max_length=10,
                        verbose_name="Número de Providencia",
                    ),
                ),
                (
                    "tipo",
                    models.CharField(
                        choices=[
                            ("incorporacion", "Incorporación"),
                            ("renovacion", "Renovación"),
                        ],
                        max_length=20,
                        verbose_name="Tipo de Admisión",
                    ),
                ),
                (
                    "cantidad_espacios",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("hasta_5", "Hasta 5 Espacios"),
                            ("mas_de_5", "Más de 5 Espacios"),
                        ],
                        max_length=10,
                        null=True,
                        verbose_name="Cantidad de Espacios",
                    ),
                ),
                (
                    "es_judicializado",
                    models.BooleanField(
                        default=False, verbose_name="¿Es Judicializado?"
                    ),
                ),
                (
                    "caratula_causa",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        null=True,
                        verbose_name="Carátula de la Causa",
                    ),
                ),
                (
                    "juzgado",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        null=True,
                        verbose_name="Juzgado",
                    ),
                ),
                (
                    "memo",
                    models.CharField(
                        blank=True, max_length=255, null=True, verbose_name="Memo"
                    ),
                ),
                (
                    "numero_pv_primera",
                    models.CharField(
                        blank=True,
                        max_length=100,
                        null=True,
                        verbose_name="Número de PV Primera Providencia",
                    ),
                ),
                (
                    "archivo",
                    models.FileField(
                        blank=True,
                        null=True,
                        upload_to="admisiones/providencias/pdf",
                    ),
                ),
                (
                    "archivo_docx",
                    models.FileField(
                        blank=True,
                        null=True,
                        upload_to="admisiones/providencias/docx",
                    ),
                ),
                (
                    "numero_gde_pv",
                    models.CharField(
                        blank=True,
                        max_length=100,
                        null=True,
                        verbose_name="Número de GDE PV",
                    ),
                ),
                ("creado", models.DateTimeField(auto_now_add=True)),
                (
                    "admision",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="providencias",
                        to="admisiones.admision",
                    ),
                ),
                (
                    "creado_por",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="admisiones_providencias",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "providencia",
                "verbose_name_plural": "providencias",
            },
        ),
        migrations.AddConstraint(
            model_name="providencia",
            constraint=models.UniqueConstraint(
                fields=("admision", "orden"),
                name="unique_providencia_por_admision_y_orden",
            ),
        ),
    ]
