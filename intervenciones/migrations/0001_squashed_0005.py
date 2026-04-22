import core.soft_delete
import django.db.models.deletion
import django.utils.timezone
import intervenciones.models.intervenciones
from django.conf import settings
from django.db import migrations, models


SUBTIPOS_FCH = [
    "Creación de Usuario en Plataforma Alimentar Comunidad",
    "Uso de Plataforma Alimentar Comunidad: Cómo consultar saldo y subir comprobantes",
    "Retiro y Uso de la Tarjeta Alimentar Comunidad",
    "Criterios Nutricionales - Alimentar Comunidad",
    "Rendición de Cuentas Resolución 650/25 - Alimentar Comunidad",
    "Gastos Accesorios 6% - Resolución 650/25 - Alimentar Comunidad",
    "Pautas de Higiene - Alimentar Comunidad",
    "Seguridad en la Cocina - Alimentar Comunidad",
]


def seed_programa_tipointervencion(apps, schema_editor):
    TipoIntervencion = apps.get_model("intervenciones", "TipoIntervencion")
    SubIntervencion = apps.get_model("intervenciones", "SubIntervencion")

    TipoIntervencion.objects.all().update(programa="comedores")

    ejemplos_cdi = [
        (
            "Entrevista inicial",
            ["Ingreso", "Actualización de datos", "Derivación interna"],
        ),
        (
            "Seguimiento familiar",
            ["Presencial", "Telefónico", "Domiciliario"],
        ),
        (
            "Articulación institucional",
            ["Escuela", "Salud", "Servicio local"],
        ),
    ]

    for tipo_nombre, subtipos in ejemplos_cdi:
        tipo, _ = TipoIntervencion.objects.get_or_create(
            nombre=tipo_nombre,
            programa="cdi",
        )
        for subtipo_nombre in subtipos:
            SubIntervencion.objects.get_or_create(
                nombre=subtipo_nombre,
                tipo_intervencion=tipo,
            )


def agregar_tipo_y_subtipos_fch(apps, schema_editor):
    TipoIntervencion = apps.get_model("intervenciones", "TipoIntervencion")
    SubIntervencion = apps.get_model("intervenciones", "SubIntervencion")

    TipoIntervencion.objects.filter(nombre="Asistencia a capacitación").update(
        nombre="Asistencia a Capacitación Sincrónica"
    )

    tipo_fch, _ = TipoIntervencion.objects.get_or_create(
        nombre="Asistencia a Capacitación Formando Capital Humano"
    )

    for nombre in SUBTIPOS_FCH:
        SubIntervencion.objects.get_or_create(
            nombre=nombre,
            tipo_intervencion=tipo_fch,
        )


def revertir_tipo_y_subtipos_fch(apps, schema_editor):
    TipoIntervencion = apps.get_model("intervenciones", "TipoIntervencion")
    SubIntervencion = apps.get_model("intervenciones", "SubIntervencion")

    TipoIntervencion.objects.filter(
        nombre="Asistencia a Capacitación Sincrónica"
    ).update(nombre="Asistencia a capacitación")

    tipo_fch = TipoIntervencion.objects.filter(
        nombre="Asistencia a Capacitación Formando Capital Humano"
    ).first()
    if tipo_fch:
        SubIntervencion.objects.filter(tipo_intervencion=tipo_fch).delete()
        tipo_fch.delete()


class Migration(migrations.Migration):

    replaces = [
        ("intervenciones", "0001_initial"),
        ("intervenciones", "0002_alter_intervencion_fecha"),
        ("intervenciones", "0003_alter_intervencion_managers_intervencion_deleted_at_and_more"),
        ("intervenciones", "0004_tipointervencion_programa"),
        ("intervenciones", "0005_tipointervencion_capacitacion_sincronica_y_fch"),
    ]

    initial = True

    dependencies = [
        ("comedores", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="TipoContacto",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=255)),
            ],
            options={
                "verbose_name": "Tipo de Contacto",
                "verbose_name_plural": "Tipos de Contacto",
                "ordering": ["id"],
            },
        ),
        migrations.CreateModel(
            name="TipoDestinatario",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=255)),
            ],
            options={
                "verbose_name": "Destinatario",
                "verbose_name_plural": "Destinatarios",
                "ordering": ["id"],
            },
        ),
        migrations.CreateModel(
            name="TipoIntervencion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=255)),
                (
                    "programa",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        help_text="Texto libre para segmentar tipos por módulo (ej: comedores, cdi).",
                        max_length=100,
                        null=True,
                        verbose_name="Programa",
                    ),
                ),
            ],
            options={
                "verbose_name": "Tipo de Intervención",
                "verbose_name_plural": "Tipos de Intervención",
                "ordering": ["id"],
            },
        ),
        migrations.CreateModel(
            name="SubIntervencion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=255)),
                (
                    "tipo_intervencion",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="subintervenciones",
                        to="intervenciones.tipointervencion",
                        verbose_name="Tipo de Intervención asociada",
                    ),
                ),
            ],
            options={
                "verbose_name": "Sub-Intervención",
                "verbose_name_plural": "Sub-Intervenciones",
                "ordering": ["tipo_intervencion", "nombre"],
            },
        ),
        migrations.CreateModel(
            name="Intervencion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "fecha",
                    models.DateTimeField(
                        default=django.utils.timezone.now,
                        validators=[intervenciones.models.intervenciones.validar_rango_anio_fecha],
                        verbose_name="Fecha y hora de intervención",
                    ),
                ),
                ("observaciones", models.TextField(blank=True, null=True, verbose_name="Observaciones")),
                ("tiene_documentacion", models.BooleanField(default=False, verbose_name="Documentación adjunta")),
                (
                    "documentacion",
                    models.FileField(
                        blank=True,
                        null=True,
                        upload_to="documentacion/",
                        verbose_name="Documentación Adjunta",
                    ),
                ),
                (
                    "comedor",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="intervenciones",
                        to="comedores.comedor",
                        verbose_name="Comedor intervenido",
                    ),
                ),
                (
                    "destinatario",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="intervenciones.tipodestinatario",
                        verbose_name="Destinatario",
                    ),
                ),
                (
                    "forma_contacto",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="intervenciones.tipocontacto",
                        verbose_name="Forma de contacto",
                    ),
                ),
                (
                    "subintervencion",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="intervenciones.subintervencion",
                        verbose_name="Sub-tipo de intervención",
                    ),
                ),
                (
                    "tipo_intervencion",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="intervenciones.tipointervencion",
                        verbose_name="Tipo de intervención",
                    ),
                ),
                ("deleted_at", models.DateTimeField(blank=True, db_index=True, null=True)),
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
            ],
            options={
                "verbose_name": "Intervención",
                "verbose_name_plural": "Intervenciones",
                "ordering": ["-fecha"],
                "indexes": [
                    models.Index(fields=["comedor"], name="intervencio_comedor_c80504_idx"),
                    models.Index(fields=["fecha"], name="intervencio_fecha_69e8fa_idx"),
                    models.Index(fields=["tipo_intervencion"], name="intervencio_tipo_in_38d798_idx"),
                ],
            },
            managers=[
                ("objects", core.soft_delete.SoftDeleteManager()),
                ("all_objects", core.soft_delete.SoftDeleteManager(include_deleted=True)),
            ],
        ),
        migrations.RunPython(seed_programa_tipointervencion, migrations.RunPython.noop),
        migrations.RunPython(agregar_tipo_y_subtipos_fch, revertir_tipo_y_subtipos_fch),
    ]
