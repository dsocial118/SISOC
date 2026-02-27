from django.db import migrations, models


def actualizar_hitos_intervenciones(apps, schema_editor):
    HitosIntervenciones = apps.get_model("acompanamientos", "HitosIntervenciones")
    HitosIntervenciones.objects.filter(
        intervencion="Asistencia a capacitación",
        subintervencion="",
        hito="Capacitación realizada",
    ).update(
        intervencion="Asistencia a Capacitación Sincrónica",
        hito="Capacitación Sincrónica Realizada",
    )


def revertir_hitos_intervenciones(apps, schema_editor):
    HitosIntervenciones = apps.get_model("acompanamientos", "HitosIntervenciones")
    HitosIntervenciones.objects.filter(
        intervencion="Asistencia a Capacitación Sincrónica",
        subintervencion="",
        hito="Capacitación Sincrónica Realizada",
    ).update(
        intervencion="Asistencia a capacitación",
        hito="Capacitación realizada",
    )


class Migration(migrations.Migration):

    dependencies = [
        ("acompanamientos", "0002_informacionrelevante_fecha_creacion"),
    ]

    operations = [
        migrations.AlterField(
            model_name="hitos",
            name="capacitacion_realizada",
            field=models.BooleanField(
                default=False, verbose_name="Capacitación Sincrónica Realizada"
            ),
        ),
        migrations.AddField(
            model_name="hitos",
            name="capacitacion_fch_realizada",
            field=models.BooleanField(
                default=False,
                verbose_name="Capacitación Formando Capital Humano Realizada",
            ),
        ),
        migrations.RunPython(
            actualizar_hitos_intervenciones,
            revertir_hitos_intervenciones,
        ),
    ]
