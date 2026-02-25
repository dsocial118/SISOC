from django.db import migrations, models


def seed_programa_tipointervencion(apps, schema_editor):
    TipoIntervencion = apps.get_model("intervenciones", "TipoIntervencion")
    SubIntervencion = apps.get_model("intervenciones", "SubIntervencion")

    # Los tipos existentes pertenecen al módulo de comedores.
    TipoIntervencion.objects.all().update(programa="comedores")

    ejemplos_cdi = [
        (
            "Entrevista inicial",
            [
                "Ingreso",
                "Actualización de datos",
                "Derivación interna",
            ],
        ),
        (
            "Seguimiento familiar",
            [
                "Presencial",
                "Telefónico",
                "Domiciliario",
            ],
        ),
        (
            "Articulación institucional",
            [
                "Escuela",
                "Salud",
                "Servicio local",
            ],
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


class Migration(migrations.Migration):

    dependencies = [
        (
            "intervenciones",
            "0003_alter_intervencion_managers_intervencion_deleted_at_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="tipointervencion",
            name="programa",
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text=(
                    "Texto libre para segmentar tipos por módulo "
                    "(ej: comedores, cdi)."
                ),
                max_length=100,
                null=True,
                verbose_name="Programa",
            ),
        ),
        migrations.RunPython(
            seed_programa_tipointervencion,
            migrations.RunPython.noop,
        ),
    ]
