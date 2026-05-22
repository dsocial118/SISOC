from django.db import migrations, models


def forwards_backfill(apps, schema_editor):
    """Inicializa ``tipo_entidad_origen`` con el ``tipo_entidad`` actual de la
    organizacion del comedor asociado. Para admisiones sin organizacion o sin
    tipo_entidad la columna queda en ``NULL`` (no hay desincronizacion posible
    hasta que la organizacion adquiera un tipo).
    """

    Admision = apps.get_model("admisiones", "Admision")
    qs = (
        Admision.objects.exclude(comedor__organizacion__tipo_entidad__isnull=True)
        .select_related("comedor__organizacion")
        .only("id", "comedor__organizacion__tipo_entidad_id")
    )
    for admision in qs.iterator(chunk_size=500):
        organizacion = getattr(getattr(admision, "comedor", None), "organizacion", None)
        tipo_id = getattr(organizacion, "tipo_entidad_id", None)
        if tipo_id and admision.tipo_entidad_origen_id != tipo_id:
            admision.tipo_entidad_origen_id = tipo_id
            admision.save(update_fields=["tipo_entidad_origen"])


class Migration(migrations.Migration):
    dependencies = [
        ("admisiones", "0058_alter_admision_estado_admision"),
        ("organizaciones", "0013_archivoorganizacion_numero_gde"),
    ]

    operations = [
        migrations.AddField(
            model_name="admision",
            name="tipo_entidad_origen",
            field=models.ForeignKey(
                blank=True,
                help_text=(
                    "Snapshot del tipo de entidad de la organizacion en el"
                    " momento en que la admision quedo sincronizada"
                    " (creacion, resync manual o aceptacion de divergencia)."
                ),
                null=True,
                on_delete=models.deletion.SET_NULL,
                related_name="admisiones_con_snapshot",
                to="organizaciones.tipoentidad",
                verbose_name="Tipo de entidad de origen",
            ),
        ),
        migrations.RunPython(forwards_backfill, migrations.RunPython.noop),
    ]
