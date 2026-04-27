from django.db import migrations


def asignar_admision_a_intervenciones(apps, schema_editor):
    """
    Para cada comedor con intervenciones, asigna la admisión más reciente
    con acompañamiento activo. Usa bulk update por comedor para minimizar
    las queries.
    """
    Intervencion = apps.get_model("intervenciones", "Intervencion")
    Acompanamiento = apps.get_model("acompanamientos", "Acompanamiento")

    comedor_ids = (
        Intervencion.all_objects.filter(admision__isnull=True, comedor__isnull=False)
        .values_list("comedor_id", flat=True)
        .distinct()
    )

    for comedor_id in comedor_ids:
        acompanamiento = (
            Acompanamiento.objects.filter(admision__comedor_id=comedor_id)
            .order_by("-admision__id")
            .select_related("admision")
            .first()
        )
        if not acompanamiento:
            continue

        Intervencion.all_objects.filter(
            comedor_id=comedor_id,
            admision__isnull=True,
        ).update(admision_id=acompanamiento.admision_id)


class Migration(migrations.Migration):

    dependencies = [
        ("acompanamientos", "0008_hitos_backfill"),
        ("intervenciones", "0006_intervencion_admision"),
    ]

    operations = [
        migrations.RunPython(
            asignar_admision_a_intervenciones,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
