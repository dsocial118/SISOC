from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


ESTADOS = [
    (
        "Activo",
        "Titular que percibe la prestacion monetaria en el ultimo mes liquidado.",
    ),
    (
        "Suspendido",
        "Titular que no percibe la prestacion monetaria por incompatibilidad "
        "o incumplimiento reversible.",
    ),
    (
        "Baja",
        "Titular dado de baja; su situacion es irreversible.",
    ),
]

AVISOS = [
    (1, "100%", "", ["Activo"]),
    (2, "50% INGRESO PROTEGIDO AL EMPLEO", "en desuso", ["Activo"]),
    (3, "50% INCUMPLIMIENTO", "en desuso", ["Activo"]),
    (4, "50% NO VALIDAR DATOS", "en desuso", ["Activo"]),
    (5, "MENOS % EMBARGO JUDICIAL", "", ["Activo"]),
    (6, "EXTRAORDINARIO", "en desuso", ["Activo"]),
    (10, "INCOMPATIBLE", "", ["Suspendido", "Baja"]),
    (11, "SIN NOVEDADES PARA EL MES LIQUIDADO", "", ["Suspendido", "Baja"]),
    (12, "CUENTA SIN MOVIMIENTO", "", ["Suspendido", "Baja"]),
    (13, "SUSPENSION POR INCUMPLIMIENTO", "en desuso", ["Suspendido", "Baja"]),
    (14, "NO VALIDO DATOS", "en desuso", ["Suspendido", "Baja"]),
    (15, "VALIDO DATOS FUERA DE TERMINO", "en desuso", ["Suspendido", "Baja"]),
    (18, "PERSONAS JURIDICAS", "", ["Suspendido", "Baja"]),
    (20, "INCOMPATIBLE AFIP (VEHICULOS)", "en desuso", ["Suspendido", "Baja"]),
    (
        21,
        "INCOMPATIBLE AFIP (JUBILACION / PENSION)",
        "en desuso",
        ["Suspendido", "Baja"],
    ),
    (22, "INCOMPATIBLE AFIP (AUTONOMOS)", "en desuso", ["Suspendido", "Baja"]),
    (
        23,
        "INCOMPATIBLE AFIP (VEHICULOS + AUTONOMOS)",
        "en desuso",
        ["Suspendido", "Baja"],
    ),
    (
        24,
        "INCOMPATIBLE AFIP (VEHICULOS + JUBILACION / PENSION)",
        "en desuso",
        ["Suspendido", "Baja"],
    ),
    (
        25,
        "INCOMPATIBLE AFIP (AUTONOMOS + JUBILACION / PENSION)",
        "en desuso",
        ["Suspendido", "Baja"],
    ),
    (26, "INSTRUCCION MINISTERIAL", "en desuso", ["Suspendido", "Baja"]),
    (27, "INFORMADO MIGRACIONES", "en desuso", ["Suspendido", "Baja"]),
    (28, "AUSENTE ACTUALIZACION DE DATOS", "en desuso", ["Suspendido", "Baja"]),
    (29, "AUSENTE SEGUNDA ACTUALIZACION DE DATOS", "en desuso", ["Suspendido", "Baja"]),
    (30, "AUSENTE TERCERA ACTUALIZACION DE DATOS", "en desuso", ["Suspendido", "Baja"]),
    (31, "CUENTA BNA CERRADA", "", ["Suspendido", "Baja"]),
    (
        32,
        "INICIAR TRAMITE JUBILATORIO O DE PENSION",
        "en desuso",
        ["Suspendido", "Baja"],
    ),
    (33, "SUSPENSION POR DENUNCIA", "", ["Suspendido", "Baja"]),
    (34, "SUSPENSION SOLICITADA POR LA UNIDAD PRODUCTIVA", "", ["Suspendido", "Baja"]),
    (35, "SUSPENSION POR NO ACTUALIZACION", "", ["Suspendido", "Baja"]),
    (36, "SUSPENSION POR OPERATIVO DE RELEVAMIENTO", "", ["Suspendido", "Baja"]),
    (37, "SUSPENSION SOLICITADA", "", ["Suspendido", "Baja"]),
    (38, "NOTIFICACION JUDICIAL", "", ["Suspendido", "Baja"]),
    (39, "RENUNCIA", "", ["Baja"]),
    (40, "FALLECIDO", "", ["Baja"]),
    (41, "NO PRESENTO FOTE", "en desuso", ["Suspendido", "Baja"]),
    (42, "INSTRUCCION MINISTERIAL EMPLEO PUBLICO", "en desuso", ["Suspendido", "Baja"]),
    (43, "INCOMPATIBLE ANSES (DESEMPLEO)", "en desuso", ["Suspendido", "Baja"]),
    (
        44,
        "INCOMPATIBLE ANSES (JUBILACION / PENSION)",
        "en desuso",
        ["Suspendido", "Baja"],
    ),
    (
        45,
        "INCOMPATIBLE ANSES (JUBILACION PROVINCIAL)",
        "en desuso",
        ["Suspendido", "Baja"],
    ),
    (46, "INCOMPATIBLE ANSES (MONOTRIBUTO)", "en desuso", ["Suspendido", "Baja"]),
    (
        47,
        "INCOMPATIBLE ANSES (PENSION NO CONTRIBUTIVA)",
        "en desuso",
        ["Suspendido", "Baja"],
    ),
    (
        48,
        "INCOMPATIBLE ANSES (PROG POTENCIAR INCLUSION JOVEN)",
        "en desuso",
        ["Suspendido", "Baja"],
    ),
    (
        49,
        "INCOMPATIBLE ANSES (PROGRAMAS NACIONALES)",
        "en desuso",
        ["Suspendido", "Baja"],
    ),
    (
        50,
        "INCOMPATIBLE ANSES (PROGRAMAS PROVINCIALES)",
        "en desuso",
        ["Suspendido", "Baja"],
    ),
    (
        51,
        "INCOMPATIBLE ANSES (RESIDE EN EXTRANJERO)",
        "en desuso",
        ["Suspendido", "Baja"],
    ),
    (
        52,
        "INCOMPATIBLE ANSES (RESIDENCIA VENCIDA)",
        "en desuso",
        ["Suspendido", "Baja"],
    ),
    (53, "INCOMPATIBLE ANSES (VEHICULOS)", "en desuso", ["Suspendido", "Baja"]),
    (55, "MIGRADO A VAT", "", ["Baja"]),
    (56, "NO CUMPLIO RELEVAMIENTO PAS", "", ["Suspendido", "Baja"]),
]


def cargar_catalogo_pas(apps, schema_editor):
    PasEstado = apps.get_model("pas", "PasEstado")
    PasAviso = apps.get_model("pas", "PasAviso")

    estados = {}
    for nombre, descripcion in ESTADOS:
        estado, _ = PasEstado.objects.update_or_create(
            nombre=nombre,
            defaults={"descripcion": descripcion},
        )
        estados[nombre] = estado

    for codigo, descripcion, observacion, nombres_estados in AVISOS:
        aviso, _ = PasAviso.objects.update_or_create(
            codigo=codigo,
            defaults={"descripcion": descripcion, "observacion": observacion},
        )
        aviso.estados.set(estados[nombre] for nombre in nombres_estados)


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("core", "0008_programa_organismo_programa_descripcion"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PasEstado",
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
                ("nombre", models.CharField(max_length=50, unique=True)),
                ("descripcion", models.TextField(blank=True)),
            ],
            options={
                "verbose_name": "Estado PAS",
                "verbose_name_plural": "Estados PAS",
                "ordering": ["nombre"],
            },
        ),
        migrations.CreateModel(
            name="PasAviso",
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
                ("codigo", models.PositiveIntegerField(unique=True)),
                ("descripcion", models.CharField(max_length=255)),
                ("observacion", models.CharField(blank=True, max_length=255)),
                (
                    "estados",
                    models.ManyToManyField(
                        related_name="avisos",
                        to="pas.pasestado",
                    ),
                ),
            ],
            options={
                "verbose_name": "Aviso PAS",
                "verbose_name_plural": "Avisos PAS",
                "ordering": ["codigo"],
            },
        ),
        migrations.CreateModel(
            name="PasPersona",
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
                    "id_persona",
                    models.PositiveIntegerField(
                        unique=True,
                        verbose_name="IdPersona",
                    ),
                ),
                ("apellidos", models.CharField(max_length=150)),
                ("nombres", models.CharField(max_length=150)),
                ("dni", models.PositiveIntegerField(unique=True)),
                ("cuit", models.CharField(blank=True, max_length=20)),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
                ("fecha_actualizacion", models.DateTimeField(auto_now=True)),
                (
                    "avisos",
                    models.ManyToManyField(
                        related_name="personas",
                        to="pas.pasaviso",
                    ),
                ),
                (
                    "estado",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="pas.pasestado",
                    ),
                ),
                (
                    "municipio",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="core.municipio",
                    ),
                ),
                (
                    "provincia",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="core.provincia",
                    ),
                ),
            ],
            options={
                "verbose_name": "Persona PAS",
                "verbose_name_plural": "Personas PAS",
                "ordering": ["apellidos", "nombres", "id_persona"],
            },
        ),
        migrations.CreateModel(
            name="PasHistorialEstado",
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
                ("fecha_cambio", models.DateTimeField(auto_now_add=True)),
                (
                    "avisos_anteriores",
                    models.ManyToManyField(
                        blank=True,
                        related_name="historiales_como_anterior",
                        to="pas.pasaviso",
                    ),
                ),
                (
                    "avisos_nuevos",
                    models.ManyToManyField(
                        related_name="historiales_como_nuevo",
                        to="pas.pasaviso",
                    ),
                ),
                (
                    "estado_anterior",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="historiales_como_anterior",
                        to="pas.pasestado",
                    ),
                ),
                (
                    "estado_nuevo",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="historiales_como_nuevo",
                        to="pas.pasestado",
                    ),
                ),
                (
                    "persona",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="historial_estados",
                        to="pas.paspersona",
                    ),
                ),
                (
                    "usuario",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Historial de estado PAS",
                "verbose_name_plural": "Historiales de estado PAS",
                "ordering": ["-fecha_cambio", "-id"],
            },
        ),
        migrations.RunPython(cargar_catalogo_pas, migrations.RunPython.noop),
    ]
