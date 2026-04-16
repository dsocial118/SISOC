"""
Data migration: vincula los Hitos existentes al Acompanamiento correspondiente.

Criterios aplicados (validados con el equipo antes del deploy):
- Por cada Admision con enviado_acompaniamiento=True se crea un Acompanamiento,
  copiando numero_convenio como nro_convenio.
- Comedores con exactamente 1 admisión enviada: vinculación directa.
- Comedores con 2+ admisiones enviadas: se vincula al Acompanamiento de la
  admisión más reciente (mayor id).
- Hitos sin ninguna admisión enviada (894 registros, 883 vacíos + 11 con datos):
  se dejan con acompanamiento=NULL. Los 11 con datos reales quedan pendientes
  de resolución manual por el equipo (ver ticket tk1273).
"""

from django.db import migrations


def migrar_acompaniamientos(apps, schema_editor):
    Admision = apps.get_model("admisiones", "Admision")
    Acompanamiento = apps.get_model("acompanamientos", "Acompanamiento")
    Hitos = apps.get_model("acompanamientos", "Hitos")

    # Crear un Acompanamiento por cada admisión enviada a acompañamiento
    for admision in Admision.objects.filter(enviado_acompaniamiento=True).order_by(
        "id"
    ):
        nro = admision.numero_convenio or (
            str(admision.convenio_numero) if admision.convenio_numero else ""
        )
        Acompanamiento.objects.get_or_create(
            admision=admision,
            defaults={"nro_convenio": nro},
        )

    # Vincular Hitos existentes al Acompanamiento más reciente del mismo comedor
    for hito in Hitos.objects.filter(
        comedor__isnull=False, acompanamiento__isnull=True
    ):
        acompanamiento = (
            Acompanamiento.objects.filter(admision__comedor_id=hito.comedor_id)
            .order_by("-admision__id")
            .first()
        )
        if acompanamiento:
            hito.acompanamiento = acompanamiento
            hito.save(update_fields=["acompanamiento"])


def revertir_acompaniamientos(apps, schema_editor):
    Acompanamiento = apps.get_model("acompanamientos", "Acompanamiento")
    Hitos = apps.get_model("acompanamientos", "Hitos")
    Hitos.objects.update(acompanamiento=None)
    Acompanamiento.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("acompanamientos", "0004_acompanamiento_model"),
    ]

    operations = [
        migrations.RunPython(
            migrar_acompaniamientos,
            revertir_acompaniamientos,
        ),
    ]
