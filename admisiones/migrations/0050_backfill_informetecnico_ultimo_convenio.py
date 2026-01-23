from django.db import migrations
from django.db.models import F

MEALS = ["desayuno", "almuerzo", "merienda", "cena"]
DAYS = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]


def forwards(apps, schema_editor):
    InformeTecnico = apps.get_model("admisiones", "InformeTecnico")
    update_kwargs = {}
    for meal in MEALS:
        for day in DAYS:
            update_kwargs[f"aprobadas_ultimo_convenio_{meal}_{day}"] = F(
                f"aprobadas_{meal}_{day}"
            )
    InformeTecnico.objects.filter(admision__tipo="renovacion").update(**update_kwargs)


class Migration(migrations.Migration):
    dependencies = [
        ("admisiones", "0049_informetecnico_prestaciones_ultimo_convenio"),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
