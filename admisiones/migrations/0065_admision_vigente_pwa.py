# Generated manually in FAST mode.

from django.db import migrations, models


def marcar_admisiones_vigentes_pwa(apps, schema_editor):
    Admision = apps.get_model("admisiones", "Admision")
    InformeTecnico = apps.get_model("admisiones", "InformeTecnico")
    comedor_ids = (
        Admision.objects.exclude(comedor_id__isnull=True)
        .values_list("comedor_id", flat=True)
        .distinct()
    )
    for comedor_id in comedor_ids:
        admisiones = Admision.objects.filter(comedor_id=comedor_id).order_by("-id")
        informe_admision_id = (
            InformeTecnico.objects.filter(
                admision__comedor_id=comedor_id,
                estado_formulario="finalizado",
            )
            .order_by("-modificado", "-id")
            .values_list("admision_id", flat=True)
            .first()
        )
        vigente = None
        if informe_admision_id:
            vigente = admisiones.filter(pk=informe_admision_id).first()
        vigente = (
            vigente or admisiones.filter(activa=True).first() or admisiones.first()
        )
        if vigente:
            Admision.objects.filter(comedor_id=comedor_id).update(vigente_pwa=False)
            Admision.objects.filter(pk=vigente.pk).update(vigente_pwa=True)


class Migration(migrations.Migration):

    dependencies = [
        ("admisiones", "0064_admision_personas_conveniadas_nomina"),
    ]

    operations = [
        migrations.AddField(
            model_name="admision",
            name="vigente_pwa",
            field=models.BooleanField(
                default=False,
                help_text="Indica que esta admision es la referencia vigente para PWA.",
                verbose_name="Vigente para PWA",
            ),
        ),
        migrations.RunPython(marcar_admisiones_vigentes_pwa, migrations.RunPython.noop),
    ]
