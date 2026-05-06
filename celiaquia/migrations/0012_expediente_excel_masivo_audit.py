from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def backfill_excel_masivo_audit(apps, _schema_editor):
    Expediente = apps.get_model("celiaquia", "Expediente")
    ExpedienteEstadoHistorial = apps.get_model("celiaquia", "ExpedienteEstadoHistorial")

    expedientes = (
        Expediente.objects.exclude(excel_masivo="")
        .exclude(excel_masivo__isnull=True)
        .only("id", "usuario_provincia_id", "fecha_creacion")
    )
    for expediente in expedientes.iterator():
        update_data = {}
        if expediente.usuario_provincia_id:
            update_data["excel_masivo_cargado_por_id"] = expediente.usuario_provincia_id
        if expediente.fecha_creacion:
            update_data["excel_masivo_cargado_en"] = expediente.fecha_creacion

        historial_procesado = (
            ExpedienteEstadoHistorial.objects.filter(
                expediente_id=expediente.pk,
                estado_nuevo__nombre="PROCESADO",
            )
            .order_by("fecha", "pk")
            .first()
        )
        if historial_procesado:
            update_data["excel_masivo_procesado_por_id"] = (
                historial_procesado.usuario_id
            )
            update_data["excel_masivo_procesado_en"] = historial_procesado.fecha

        if update_data:
            Expediente.objects.filter(pk=expediente.pk).update(**update_data)


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("celiaquia", "0011_alter_expediente_managers"),
    ]

    operations = [
        migrations.AddField(
            model_name="expediente",
            name="excel_masivo_cargado_por",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="expediente",
            name="excel_masivo_cargado_en",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="expediente",
            name="excel_masivo_procesado_por",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="expediente",
            name="excel_masivo_procesado_en",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(backfill_excel_masivo_audit, migrations.RunPython.noop),
    ]
