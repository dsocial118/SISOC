import random

from django.contrib.auth import get_user_model

from VAT.models import AsistenciaSesion, Inscripcion

random.seed(123)
admin = get_user_model().objects.get(username="admin_preview")

created_count = 0
for inscripcion in Inscripcion.objects.filter(comision_curso__codigo_comision__startswith="DUMI-COM-"):
    sesiones = list(inscripcion.comision_curso.sesiones.all())
    random.shuffle(sesiones)
    for sesion in sesiones[: random.randint(2, 4)]:
        _, created = AsistenciaSesion.objects.get_or_create(
            sesion=sesion,
            inscripcion=inscripcion,
            defaults={
                "presente": random.choice([True, True, False]),
                "registrado_por": admin,
                "observaciones": "Carga dummy",
            },
        )
        if created:
            created_count += 1

print({"asistencias_nuevas": created_count})
