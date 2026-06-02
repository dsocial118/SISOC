"""Issue #1799 Req 3: el Numero de GDE pasa a ser propiedad del legajo de la
Organizacion (unica fuente). Backfill best-effort de ``ArchivoOrganizacion.numero_gde``
desde el modelo per-admision ``NumeroGdeOrganizacion`` (introducido por #1605) y,
en su defecto, desde el GDE cargado directamente en los ``ArchivoAdmision``
materializados.

Resolucion de conflictos: si distintas admisiones tenian GDE distinto para el
mismo documento de organizacion, prevalece el mas reciente (no hay forma univoca
de revertir un modelo 1->N). ``NumeroGdeOrganizacion`` no se borra (queda como
historico). Reverse: no-op."""

from django.db import migrations
from django.db.models import Q


def backfill_gde_a_organizacion(apps, schema_editor):
    ArchivoOrganizacion = apps.get_model("organizaciones", "ArchivoOrganizacion")
    NumeroGdeOrganizacion = apps.get_model("admisiones", "NumeroGdeOrganizacion")
    ArchivoAdmision = apps.get_model("admisiones", "ArchivoAdmision")

    vacio = Q(numero_gde__isnull=True) | Q(numero_gde="")

    # 1) NumeroGdeOrganizacion es la fuente activa post-#1605. El valor mas
    #    reciente por archivo_organizacion prevalece (orden ascendente: el ultimo
    #    update gana).
    regs = (
        NumeroGdeOrganizacion.objects.exclude(numero_gde__isnull=True)
        .exclude(numero_gde="")
        .order_by("modificado")
    )
    for reg in regs.iterator(chunk_size=500):
        ArchivoOrganizacion.objects.filter(id=reg.archivo_organizacion_id).update(
            numero_gde=reg.numero_gde
        )

    # 2) Fallback: GDE cargado directamente en un ArchivoAdmision materializado,
    #    solo si el ArchivoOrganizacion de origen sigue sin valor.
    mats = (
        ArchivoAdmision.objects.filter(archivo_organizacion_origen__isnull=False)
        .exclude(numero_gde__isnull=True)
        .exclude(numero_gde="")
        .order_by("id")
    )
    for adm in mats.iterator(chunk_size=500):
        ArchivoOrganizacion.objects.filter(
            id=adm.archivo_organizacion_origen_id
        ).filter(vacio).update(numero_gde=adm.numero_gde)


class Migration(migrations.Migration):

    dependencies = [
        ("admisiones", "0061_archivoadmision_archivo_organizacion_origen"),
    ]

    operations = [
        migrations.RunPython(backfill_gde_a_organizacion, migrations.RunPython.noop),
    ]
