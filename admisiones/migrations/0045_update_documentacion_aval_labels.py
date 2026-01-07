from django.db import migrations


def update_documentacion_aval_labels(apps, schema_editor):
    Documentacion = apps.get_model("admisiones", "Documentacion")

    renames = {
        "DNI Autoridad Máxima - Aval 1": "DNI Autoridad Máxima Aval 1- DNI Aval 1 (persona física)",
        "DNI Autoridad Máxima Aval 1": "DNI Autoridad Máxima Aval 1- DNI Aval 1 (persona física)",
        "DNI Autoridad Máxima - Aval 2": "DNI Autoridad Máxima Aval 2 - DNI Aval 2 (persona física)",
        "DNI Autoridad Máxima Aval 2": "DNI Autoridad Máxima Aval 2 - DNI Aval 2 (persona física)",
        "Acta Designación - Aval 1": "Acta Designación Aval 1 - Designación de cargo Aval 1 (persona física)",
        "Acta Designación Aval 1": "Acta Designación Aval 1 - Designación de cargo Aval 1 (persona física)",
        "Acta Designación - Aval 2": "Acta Designación Aval 2 - Designación de cargo Aval 2 (persona física)",
        "Acta Designación Aval 2": "Acta Designación Aval 2 - Designación de cargo Aval 2 (persona física)",
        "Aval 1": "Nota Aval 1",
        "Aval 2": "Nota Aval 2",
    }

    for old_name, new_name in renames.items():
        Documentacion.objects.filter(nombre=old_name).update(nombre=new_name)

    optional_names = [
        "Acta constitutiva - Aval 1",
        "Acta constitutiva Aval 1",
        "Acta constitutiva - Aval 2",
        "Acta constitutiva Aval 2",
        "Estatuto - Aval 1",
        "Estatuto Aval 1",
        "Estatuto - Aval 2",
        "Estatuto Aval 2",
        "Reso Personería Jurídica - Aval 1",
        "Reso Personería Jurídica Aval 1",
        "Reso Personería Jurídica - Aval 2",
        "Reso Personería Jurídica Aval 2",
    ]
    Documentacion.objects.filter(nombre__in=optional_names).update(obligatorio=False)


class Migration(migrations.Migration):

    dependencies = [
        ("admisiones", "0044_alter_informetecnico_creado_por_and_more"),
    ]

    operations = [
        migrations.RunPython(update_documentacion_aval_labels, migrations.RunPython.noop),
    ]
