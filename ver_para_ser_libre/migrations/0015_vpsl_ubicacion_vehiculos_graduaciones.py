from decimal import Decimal

import django.core.validators
from django.db import migrations, models


VEHICULOS_INICIALES = (
    ("vehiculo_1", "Vehiculo 1", 1),
    ("vehiculo_2", "Vehiculo 2", 2),
    ("vehiculo_3", "Vehiculo 3", 3),
    ("vehiculo_4", "Vehiculo 4", 4),
)


def crear_catalogo_y_migrar_vehiculos(apps, schema_editor):
    vehiculo_model = apps.get_model("ver_para_ser_libre", "VehiculoVPSL")
    jornada_model = apps.get_model("ver_para_ser_libre", "JornadaVPSL")
    vehiculos_por_codigo = {}
    for codigo, nombre, orden in VEHICULOS_INICIALES:
        vehiculo, _ = vehiculo_model.objects.update_or_create(
            nombre=nombre,
            defaults={"orden": orden, "activo": True},
        )
        vehiculos_por_codigo[codigo] = vehiculo

    for jornada in jornada_model.objects.exclude(vehiculo="").iterator():
        vehiculo = vehiculos_por_codigo.get(jornada.vehiculo)
        if vehiculo:
            jornada.vehiculos.add(vehiculo)


def restaurar_vehiculo_singular(apps, schema_editor):
    jornada_model = apps.get_model("ver_para_ser_libre", "JornadaVPSL")
    codigos_por_nombre = {
        nombre: codigo for codigo, nombre, _orden in VEHICULOS_INICIALES
    }
    for jornada in jornada_model.objects.prefetch_related("vehiculos").iterator(
        chunk_size=200
    ):
        primer_vehiculo = jornada.vehiculos.order_by("orden", "nombre", "pk").first()
        jornada.vehiculo = (
            codigos_por_nombre.get(primer_vehiculo.nombre, "")
            if primer_vehiculo
            else ""
        )
        jornada.save(update_fields=["vehiculo"])


class Migration(migrations.Migration):
    replaces = [
        ("ver_para_ser_libre", "0015_jornada_ubicacion"),
        ("ver_para_ser_libre", "0016_jornadavpsl_vehiculos"),
        ("ver_para_ser_libre", "0017_registronominalvpsl_graduaciones"),
        ("ver_para_ser_libre", "0018_vehiculovpsl_catalogo"),
        ("ver_para_ser_libre", "0019_vehiculovpsl_codigo_automatico"),
        ("ver_para_ser_libre", "0020_jornada_vehiculos_m2m"),
    ]

    dependencies = [
        ("ver_para_ser_libre", "0014_sedevpsl_optional_school_data"),
    ]

    operations = [
        migrations.AddField(
            model_name="jornadavpsl",
            name="ubicacion_url",
            field=models.URLField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name="jornadavpsl",
            name="latitud",
            field=models.DecimalField(
                blank=True, decimal_places=6, max_digits=9, null=True
            ),
        ),
        migrations.AddField(
            model_name="jornadavpsl",
            name="longitud",
            field=models.DecimalField(
                blank=True, decimal_places=6, max_digits=9, null=True
            ),
        ),
        migrations.AddField(
            model_name="registronominalvpsl",
            name="graduacion_derecha",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=3,
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(Decimal("-6")),
                    django.core.validators.MaxValueValidator(Decimal("6")),
                ],
            ),
        ),
        migrations.AddField(
            model_name="registronominalvpsl",
            name="graduacion_izquierda",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=3,
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(Decimal("-6")),
                    django.core.validators.MaxValueValidator(Decimal("6")),
                ],
            ),
        ),
        migrations.CreateModel(
            name="VehiculoVPSL",
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
                ("nombre", models.CharField(max_length=100, unique=True)),
                ("orden", models.PositiveSmallIntegerField(default=0)),
                ("activo", models.BooleanField(default=True)),
            ],
            options={
                "verbose_name": "Vehiculo VPSL",
                "verbose_name_plural": "Vehiculos VPSL",
                "ordering": ["orden", "nombre", "pk"],
            },
        ),
        migrations.AddField(
            model_name="jornadavpsl",
            name="vehiculos",
            field=models.ManyToManyField(
                blank=True,
                related_name="jornadas",
                to="ver_para_ser_libre.vehiculovpsl",
            ),
        ),
        migrations.RunPython(
            crear_catalogo_y_migrar_vehiculos,
            reverse_code=restaurar_vehiculo_singular,
        ),
        migrations.RemoveField(
            model_name="jornadavpsl",
            name="vehiculo",
        ),
    ]
