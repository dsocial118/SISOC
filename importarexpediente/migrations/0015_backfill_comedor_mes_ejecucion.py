from django.db import migrations
from django.db.models import Case, IntegerField, OuterRef, Subquery, Value, When


MES_PAGO_ALIASES = (
    (1, ("enero", "1", "01")),
    (2, ("febrero", "2", "02")),
    (3, ("marzo", "3", "03")),
    (4, ("abril", "4", "04")),
    (5, ("mayo", "5", "05")),
    (6, ("junio", "6", "06")),
    (7, ("julio", "7", "07")),
    (8, ("agosto", "8", "08")),
    (9, ("septiembre", "setiembre", "9", "09")),
    (10, ("octubre", "10")),
    (11, ("noviembre", "11")),
    (12, ("diciembre", "12")),
)


def backfill_mes_ejecucion(apps, schema_editor):
    Comedor = apps.get_model("comedores", "Comedor")
    ExpedientePago = apps.get_model("expedientespagos", "ExpedientePago")

    mes_order = Case(
        *[
            When(mes_pago__iexact=alias, then=Value(numero))
            for numero, aliases in MES_PAGO_ALIASES
            for alias in aliases
        ],
        default=Value(0),
        output_field=IntegerField(),
    )
    ultimo_mes = (
        ExpedientePago.objects.filter(comedor_id=OuterRef("pk"))
        .annotate(_mes_pago_order=mes_order)
        .order_by("-ano", "-_mes_pago_order", "-fecha_creacion", "-id")
        .values("mes_convenio")[:1]
    )
    Comedor.objects.filter(programa_id=2).update(
        mes_ejecucion=Subquery(ultimo_mes, output_field=IntegerField())
    )


class Migration(migrations.Migration):

    dependencies = [
        ("comedores", "0048_comedor_mes_ejecucion"),
        ("expedientespagos", "0002_expedientepago_total_prestaciones_and_more"),
        ("importarexpediente", "0014_archivosimportados_periodo_pago"),
    ]

    operations = [
        migrations.RunPython(backfill_mes_ejecucion, migrations.RunPython.noop),
    ]
