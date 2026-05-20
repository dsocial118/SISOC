import re

from django.db import migrations


def backfill_calle_altura_telefono(apps, schema_editor):
    Dispositivo = apps.get_model("dispositivos", "Dispositivo")
    for dispositivo in Dispositivo.objects.all():
        if dispositivo.domicilio_institucion and not dispositivo.calle:
            dispositivo.calle = dispositivo.domicilio_institucion
        if dispositivo.telefono_contacto and not dispositivo.telefono_numero:
            dispositivo.telefono_numero = re.sub(r"\D", "", dispositivo.telefono_contacto)
        dispositivo.save(update_fields=["calle", "telefono_numero"])


def reverse_backfill(apps, schema_editor):
    Dispositivo = apps.get_model("dispositivos", "Dispositivo")
    Dispositivo.objects.update(calle="", altura="", telefono_prefijo="", telefono_numero="")


class Migration(migrations.Migration):

    dependencies = [
        ("dispositivos", "0005_dispositivo_altura_dispositivo_calle_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill_calle_altura_telefono, reverse_backfill),
    ]
