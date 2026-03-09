from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from pwa.models import ActividadEspacioPWA, InscriptoActividadEspacioPWA
from pwa.services.auditoria_operacion_service import registrar_evento_operacion


def _snapshot_actividad(actividad: ActividadEspacioPWA) -> dict:
    return {
        "id": actividad.id,
        "comedor_id": actividad.comedor_id,
        "catalogo_actividad_id": actividad.catalogo_actividad_id,
        "dia_actividad_id": actividad.dia_actividad_id,
        "horario_actividad": actividad.horario_actividad,
        "activo": actividad.activo,
        "fecha_baja": actividad.fecha_baja,
    }


def _snapshot_inscripto(inscripto: InscriptoActividadEspacioPWA) -> dict:
    return {
        "id": inscripto.id,
        "actividad_espacio_id": inscripto.actividad_espacio_id,
        "nomina_id": inscripto.nomina_id,
        "activo": inscripto.activo,
        "fecha_baja": inscripto.fecha_baja,
    }


@transaction.atomic
def create_actividad_espacio(
    *, comedor_id: int, actor, data: dict
) -> ActividadEspacioPWA:
    actividad = ActividadEspacioPWA.objects.create(
        comedor_id=comedor_id,
        catalogo_actividad=data["catalogo_actividad"],
        dia_actividad=data["dia_actividad"],
        horario_actividad=data["horario_actividad"],
        creado_por=actor,
        actualizado_por=actor,
    )
    registrar_evento_operacion(
        actor=actor,
        comedor_id=comedor_id,
        entidad="actividad",
        entidad_id=actividad.id,
        accion="create",
        snapshot_despues=_snapshot_actividad(actividad),
    )
    return actividad


@transaction.atomic
def update_actividad_espacio(*, actividad: ActividadEspacioPWA, actor, data: dict):
    snapshot_antes = _snapshot_actividad(actividad)
    fields_updated = []
    for field in ("catalogo_actividad", "dia_actividad", "horario_actividad"):
        if field in data:
            setattr(actividad, field, data[field])
            fields_updated.append(field)
    actividad.actualizado_por = actor
    fields_updated.append("actualizado_por")
    fields_updated.append("fecha_actualizacion")
    actividad.save(update_fields=fields_updated)
    registrar_evento_operacion(
        actor=actor,
        comedor_id=actividad.comedor_id,
        entidad="actividad",
        entidad_id=actividad.id,
        accion="update",
        snapshot_antes=snapshot_antes,
        snapshot_despues=_snapshot_actividad(actividad),
    )
    return actividad


@transaction.atomic
def soft_delete_actividad_espacio(*, actividad: ActividadEspacioPWA, actor):
    if not actividad.activo:
        raise ValidationError("La actividad ya se encuentra inactiva.")

    snapshot_antes = _snapshot_actividad(actividad)
    now = timezone.now()
    actividad.activo = False
    actividad.fecha_baja = now
    actividad.actualizado_por = actor
    actividad.save(
        update_fields=[
            "activo",
            "fecha_baja",
            "actualizado_por",
            "fecha_actualizacion",
        ]
    )

    inscriptos_activos = list(
        InscriptoActividadEspacioPWA.objects.filter(
            actividad_espacio=actividad,
            activo=True,
        )
    )
    snapshots_antes_inscriptos = {
        inscripto.id: _snapshot_inscripto(inscripto) for inscripto in inscriptos_activos
    }
    InscriptoActividadEspacioPWA.objects.filter(
        actividad_espacio=actividad,
        activo=True,
    ).update(
        activo=False,
        fecha_baja=now,
        actualizado_por=actor,
        fecha_actualizacion=now,
    )
    registrar_evento_operacion(
        actor=actor,
        comedor_id=actividad.comedor_id,
        entidad="actividad",
        entidad_id=actividad.id,
        accion="delete",
        snapshot_antes=snapshot_antes,
        snapshot_despues=_snapshot_actividad(actividad),
    )
    for inscripto in inscriptos_activos:
        registrar_evento_operacion(
            actor=actor,
            comedor_id=actividad.comedor_id,
            entidad="inscripcion_actividad",
            entidad_id=inscripto.id,
            accion="deactivate",
            snapshot_antes=snapshots_antes_inscriptos.get(inscripto.id),
            snapshot_despues={
                **snapshots_antes_inscriptos.get(inscripto.id, {}),
                "activo": False,
                "fecha_baja": now,
            },
            metadata={"motivo": "actividad_baja"},
        )

    return actividad
