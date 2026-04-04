import re
from datetime import datetime, timedelta

from django.db import migrations, models


TIME_RANGE_REGEX = re.compile(
    r"^(?P<start>\d{1,2}:\d{2})(?:\s*(?:a|-)\s*(?P<end>\d{1,2}:\d{2}))?$"
)


def _parse_schedule(raw_value):
    value = (raw_value or "").strip()
    if not value:
        return None, None

    match = TIME_RANGE_REGEX.fullmatch(value)
    if not match:
        return None, None

    start_time = datetime.strptime(match.group("start"), "%H:%M").time()
    end_raw = match.group("end")
    end_time = datetime.strptime(end_raw, "%H:%M").time() if end_raw else None
    return start_time, end_time


def _infer_end_time(start_time, raw_duration):
    duration = (raw_duration or "").strip().lower()
    if not duration:
        return None

    minutes_match = re.search(r"(\d+)\s*min", duration)
    hours_match = re.search(r"(\d+)\s*hora", duration)
    total_minutes = 0
    if hours_match:
        total_minutes += int(hours_match.group(1)) * 60
    if minutes_match:
        total_minutes += int(minutes_match.group(1))
    if total_minutes <= 0:
        return None

    start_dt = datetime.combine(datetime.today().date(), start_time)
    return (start_dt + timedelta(minutes=total_minutes)).time()


def forwards(apps, schema_editor):
    ActividadEspacioPWA = apps.get_model("pwa", "ActividadEspacioPWA")

    for actividad in ActividadEspacioPWA.objects.all().iterator():
        start_time, end_time = _parse_schedule(actividad.horario_actividad)
        if start_time and end_time is None:
            end_time = _infer_end_time(start_time, actividad.duracion_actividad)
        if start_time and end_time is None:
            start_dt = datetime.combine(datetime.today().date(), start_time)
            end_time = (start_dt + timedelta(hours=1)).time()
        if not start_time:
            continue

        actividad.hora_inicio = start_time
        actividad.hora_fin = end_time
        actividad.horario_actividad = (
            f"{start_time.strftime('%H:%M')} a {end_time.strftime('%H:%M')}"
            if end_time
            else start_time.strftime("%H:%M")
        )
        actividad.save(update_fields=["hora_inicio", "hora_fin", "horario_actividad"])


def backwards(apps, schema_editor):
    ActividadEspacioPWA = apps.get_model("pwa", "ActividadEspacioPWA")

    for actividad in ActividadEspacioPWA.objects.all().iterator():
        if actividad.hora_inicio and actividad.hora_fin:
            actividad.horario_actividad = (
                f"{actividad.hora_inicio.strftime('%H:%M')} a "
                f"{actividad.hora_fin.strftime('%H:%M')}"
            )
            actividad.save(update_fields=["horario_actividad"])


class Migration(migrations.Migration):

    dependencies = [
        ("pwa", "0010_actividadespaciopwa_duracion_actividad"),
    ]

    operations = [
        migrations.AddField(
            model_name="actividadespaciopwa",
            name="hora_fin",
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="actividadespaciopwa",
            name="hora_inicio",
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.RunPython(forwards, backwards),
    ]
