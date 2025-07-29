from django.db import migrations, models


def forwards(apps, schema_editor):
    Relevamiento = apps.get_model("relevamientos", "Relevamiento")
    through = Relevamiento.prestaciones.through  # tabla intermedia

    rows = []
    for r in Relevamiento.objects.exclude(prestacion__isnull=True).only(
        "id", "prestacion_id"
    ):
        rows.append(through(relevamiento_id=r.id, prestacion_id=r.prestacion_id))
    if rows:
        through.objects.bulk_create(rows, ignore_conflicts=True)


def cleanup_prestacion_ids(apps, schema_editor):
    Relevamiento = apps.get_model("relevamientos", "Relevamiento")
    Prestacion = apps.get_model("core", "Prestacion")
    # pone a NULL los prestacion_id que NO existan en core_prestacion
    invalid_qs = Relevamiento.objects.exclude(
        prestacion_id__in=Prestacion.objects.values_list("id", flat=True)
    ).exclude(prestacion_id__isnull=True)
    invalid_qs.update(prestacion_id=None)


def backwards(apps, schema_editor):
    Relevamiento = apps.get_model("relevamientos", "Relevamiento")
    # Si hay varias prestaciones, elegimos la primera para restaurar el OneToOne
    for r in Relevamiento.objects.all().only("id"):
        first = r.prestaciones.first()
        if first:
            r.prestacion_id = first.id
            r.save(update_fields=["prestacion_id"])


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0004_prestacion_merienda_reforzada_and_more"),
        ("relevamientos", "0004_alter_relevamiento_prestacion"),
    ]

    operations = [
        migrations.AddField(
            model_name="relevamiento",
            name="prestaciones",
            field=models.ManyToManyField(
                blank=True,
                related_name="relevamientos",
                to="core.prestacion",
                verbose_name="Prestaciones",
            ),
        ),
        migrations.RunPython(forwards, backwards),
        migrations.RunPython(
            cleanup_prestacion_ids, reverse_code=migrations.RunPython.noop
        ),
        migrations.RemoveField(model_name="relevamiento", name="prestacion"),
    ]
