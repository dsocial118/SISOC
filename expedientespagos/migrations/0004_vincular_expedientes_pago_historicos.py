"""Vincula el histórico de expedientes de pago con su admisión.

Es la primera corrida de la misma lógica que usa el comando
``revincular_expedientes_pago`` y el signal de ``Admision``.

Medido sobre producción antes de escribirla: de 3.266 expedientes activos, 2.162
resuelven contra una admisión del mismo comedor. Los 1.104 restantes quedan en
``null`` a propósito — 1.090 apuntan a expedientes que no existen en la tabla de
admisiones, así que no hay a qué vincularlos. Se ven en el listado con la
etiqueta "Sin admisión".

La operación solo completa un campo nullable que hoy está vacío; no borra ni pisa
nada. La reversa es un no-op: desvincular en masa borraría también las
asignaciones hechas a mano.
"""

from django.db import migrations


def _normalizar(valor):
    """Copia local de la normalización para no atar la migración al código vivo."""
    if not valor:
        return ""
    texto = str(valor).strip().upper()
    for separador in (" ", "-", "/", "."):
        texto = texto.replace(separador, "")
    return texto


def vincular_historico(apps, schema_editor):
    del schema_editor
    ExpedientePago = apps.get_model("expedientespagos", "ExpedientePago")
    Admision = apps.get_model("admisiones", "Admision")

    sueltos = ExpedientePago.objects.filter(
        admision__isnull=True, comedor__isnull=False
    ).only("id", "comedor_id", "expediente_convenio")

    # Índice por comedor para no consultar admisiones una vez por expediente.
    expedientes_por_comedor = {}
    for expediente in sueltos.iterator():
        clave = _normalizar(expediente.expediente_convenio)
        if not clave:
            continue
        expedientes_por_comedor.setdefault(expediente.comedor_id, []).append(
            (expediente.id, clave)
        )

    if not expedientes_por_comedor:
        return

    admisiones_por_comedor = {}
    for admision in Admision.objects.filter(
        comedor_id__in=expedientes_por_comedor.keys()
    ).only("id", "comedor_id", "num_expediente"):
        clave = _normalizar(admision.num_expediente)
        if not clave:
            continue
        admisiones_por_comedor.setdefault(admision.comedor_id, {}).setdefault(
            clave, []
        ).append(admision.id)

    for comedor_id, expedientes in expedientes_por_comedor.items():
        candidatas = admisiones_por_comedor.get(comedor_id, {})
        for expediente_id, clave in expedientes:
            coincidencias = candidatas.get(clave, [])
            # Con cero o con varias se deja sin asignar: no se adivina.
            if len(coincidencias) == 1:
                ExpedientePago.objects.filter(id=expediente_id).update(
                    admision_id=coincidencias[0]
                )


class Migration(migrations.Migration):

    dependencies = [
        ("expedientespagos", "0003_expedientepago_admision"),
        ("admisiones", "0001_squashed_0058"),
    ]

    operations = [
        migrations.RunPython(
            vincular_historico,
            migrations.RunPython.noop,
        ),
    ]
