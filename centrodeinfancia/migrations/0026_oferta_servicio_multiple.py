from django.db import migrations, models


OFERTA_SERVICIOS = [
    ("lactantes", "Lactantes"),
    ("deambuladores", "Deambuladores"),
    ("dos_anos", "2 años"),
    ("tres_anos", "3 años"),
    ("cuatro_anos", "4 años"),
    ("multiedad", "Multiedad"),
]


def forwards_migrate_oferta_servicios(apps, schema_editor):
    CentroDeInfancia = apps.get_model("centrodeinfancia", "CentroDeInfancia")
    OfertaServicio = apps.get_model("centrodeinfancia", "OfertaServicio")

    ofertas_por_codigo = {}
    for orden, (codigo, _) in enumerate(OFERTA_SERVICIOS):
        oferta, _ = OfertaServicio.objects.get_or_create(
            codigo=codigo,
            defaults={"orden": orden},
        )
        ofertas_por_codigo[codigo] = oferta

    for centro in CentroDeInfancia.objects.exclude(oferta_servicios__isnull=True).exclude(
        oferta_servicios=""
    ):
        codigo = centro.oferta_servicios
        oferta = ofertas_por_codigo.get(codigo)
        if oferta:
            centro.oferta_servicios_m2m.set([oferta])


class Migration(migrations.Migration):

    dependencies = [
        ("centrodeinfancia", "0025_alter_centrodeinfancia_fecha_inicio_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="OfertaServicio",
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
                    "codigo",
                    models.CharField(
                        choices=[
                            ("lactantes", "Lactantes"),
                            ("deambuladores", "Deambuladores"),
                            ("dos_anos", "2 años"),
                            ("tres_anos", "3 años"),
                            ("cuatro_anos", "4 años"),
                            ("multiedad", "Multiedad"),
                        ],
                        max_length=32,
                        unique=True,
                    ),
                ),
                ("orden", models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                "verbose_name": "Oferta de servicio del CDI",
                "verbose_name_plural": "Ofertas de servicio del CDI",
                "ordering": ["orden", "codigo"],
            },
        ),
        migrations.AddField(
            model_name="centrodeinfancia",
            name="oferta_servicios_m2m",
            field=models.ManyToManyField(
                blank=True,
                related_name="centros",
                to="centrodeinfancia.ofertaservicio",
            ),
        ),
        migrations.RunPython(
            forwards_migrate_oferta_servicios,
            migrations.RunPython.noop,
        ),
        migrations.RemoveField(
            model_name="centrodeinfancia",
            name="oferta_servicios",
        ),
        migrations.RenameField(
            model_name="centrodeinfancia",
            old_name="oferta_servicios_m2m",
            new_name="oferta_servicios",
        ),
    ]
