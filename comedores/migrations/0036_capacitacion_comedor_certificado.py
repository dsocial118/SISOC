from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("comedores", "0035_merge_20260331_1500"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CapacitacionComedorCertificado",
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
                    "capacitacion",
                    models.CharField(
                        choices=[
                            (
                                "creacion_usuario_plataforma",
                                "Creación de Usuario en Plataforma Alimentar Comunidad",
                            ),
                            (
                                "criterios_nutricionales",
                                "Criterios Nutricionales - Alimentar Comunidad",
                            ),
                            (
                                "gastos_accesorios_6",
                                "Gastos Accesorios 6% - Resolución 650/25 - Alimentar Comunidad",
                            ),
                            (
                                "pautas_higiene",
                                "Pautas de Higiene - Alimentar Comunidad",
                            ),
                            (
                                "rendicion_cuentas_650_25",
                                "Rendición de Cuentas Resolución 650/25 - Alimentar Comunidad",
                            ),
                            (
                                "retiro_uso_tarjeta",
                                "Retiro y Uso de la Tarjeta Alimentar Comunidad",
                            ),
                            (
                                "seguridad_cocina",
                                "Seguridad en la Cocina - Alimentar Comunidad",
                            ),
                            (
                                "uso_plataforma_consulta_saldo_comprobantes",
                                "Uso de Plataforma Alimentar Comunidad: Cómo consultar saldo y subir comprobantes",
                            ),
                        ],
                        max_length=80,
                    ),
                ),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("sin_presentar", "SIN PRESENTAR"),
                            ("presentado", "PRESENTADO"),
                            ("rechazado", "RECHAZADO"),
                            ("aceptado", "ACEPTADO"),
                        ],
                        default="sin_presentar",
                        max_length=20,
                    ),
                ),
                (
                    "archivo",
                    models.FileField(
                        blank=True,
                        null=True,
                        upload_to="comedores/capacitaciones/",
                    ),
                ),
                ("observacion", models.TextField(blank=True, null=True)),
                ("fecha_presentacion", models.DateTimeField(blank=True, null=True)),
                ("fecha_revision", models.DateTimeField(blank=True, null=True)),
                ("creado", models.DateTimeField(auto_now_add=True)),
                ("modificado", models.DateTimeField(auto_now=True)),
                (
                    "comedor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="certificados_capacitacion",
                        to="comedores.comedor",
                    ),
                ),
                (
                    "presentado_por",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="certificados_capacitacion_presentados",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "revisado_por",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="certificados_capacitacion_revisados",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Certificado de Capacitación del Comedor",
                "verbose_name_plural": "Certificados de Capacitaciones del Comedor",
                "ordering": ["comedor_id", "capacitacion"],
            },
        ),
        migrations.AddConstraint(
            model_name="capacitacioncomedorcertificado",
            constraint=models.UniqueConstraint(
                fields=("comedor", "capacitacion"),
                name="uniq_certificado_capacitacion_por_comedor",
            ),
        ),
    ]
