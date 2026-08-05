from django.db import migrations, models
from django.db.models import Count


def normalizar_expedientes_vacios(apps, schema_editor):
    Admision = apps.get_model("admisiones", "Admision")
    Admision.objects.filter(num_expediente="").update(num_expediente=None)
    duplicados = list(
        Admision.objects.exclude(num_expediente__isnull=True)
        .values("num_expediente")
        .annotate(total=Count("pk"))
        .filter(total__gt=1)
        .values_list("num_expediente", flat=True)[:10]
    )
    if duplicados:
        raise RuntimeError(
            "No se puede aplicar la unicidad de expedientes: existen valores "
            f"duplicados ({', '.join(duplicados)})."
        )


class Migration(migrations.Migration):
    dependencies = [
        ("admisiones", "0075_alter_admision_legales_num_if"),
    ]

    operations = [
        migrations.RunPython(normalizar_expedientes_vacios, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="admision",
            constraint=models.UniqueConstraint(
                fields=("num_expediente",),
                name="uniq_admision_num_expediente",
            ),
        ),
    ]
