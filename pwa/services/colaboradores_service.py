from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from pwa.models import ColaboradorEspacioPWA
from pwa.services.auditoria_operacion_service import registrar_evento_operacion


def _snapshot_colaborador(colaborador: ColaboradorEspacioPWA) -> dict:
    return {
        "id": colaborador.id,
        "comedor_id": colaborador.comedor_id,
        "nombre": colaborador.nombre,
        "apellido": colaborador.apellido,
        "dni": colaborador.dni,
        "telefono": colaborador.telefono,
        "email": colaborador.email,
        "rol_funcion": colaborador.rol_funcion,
        "activo": colaborador.activo,
        "fecha_baja": colaborador.fecha_baja,
    }


@transaction.atomic
def create_colaborador(*, comedor_id: int, actor, data: dict) -> ColaboradorEspacioPWA:
    colaborador = (
        ColaboradorEspacioPWA.objects.filter(
            comedor_id=comedor_id,
            dni=data["dni"],
            activo=False,
        )
        .order_by("-id")
        .first()
    )
    if colaborador:
        colaborador.nombre = data["nombre"]
        colaborador.apellido = data["apellido"]
        colaborador.telefono = data["telefono"]
        colaborador.email = data["email"]
        colaborador.rol_funcion = data["rol_funcion"]
        colaborador.activo = True
        colaborador.fecha_baja = None
        colaborador.actualizado_por = actor
        colaborador.save(
            update_fields=[
                "nombre",
                "apellido",
                "telefono",
                "email",
                "rol_funcion",
                "activo",
                "fecha_baja",
                "actualizado_por",
                "fecha_actualizacion",
            ]
        )
    else:
        colaborador = ColaboradorEspacioPWA.objects.create(
            comedor_id=comedor_id,
            nombre=data["nombre"],
            apellido=data["apellido"],
            dni=data["dni"],
            telefono=data["telefono"],
            email=data["email"],
            rol_funcion=data["rol_funcion"],
            creado_por=actor,
            actualizado_por=actor,
        )
    registrar_evento_operacion(
        actor=actor,
        comedor_id=comedor_id,
        entidad="colaborador",
        entidad_id=colaborador.id,
        accion="create",
        snapshot_despues=_snapshot_colaborador(colaborador),
    )
    return colaborador


@transaction.atomic
def update_colaborador(*, colaborador: ColaboradorEspacioPWA, actor, data: dict):
    snapshot_antes = _snapshot_colaborador(colaborador)
    fields_updated = []
    for field in ("nombre", "apellido", "dni", "telefono", "email", "rol_funcion"):
        if field in data:
            setattr(colaborador, field, data[field])
            fields_updated.append(field)
    colaborador.actualizado_por = actor
    fields_updated.append("actualizado_por")
    fields_updated.append("fecha_actualizacion")
    colaborador.save(update_fields=fields_updated)
    registrar_evento_operacion(
        actor=actor,
        comedor_id=colaborador.comedor_id,
        entidad="colaborador",
        entidad_id=colaborador.id,
        accion="update",
        snapshot_antes=snapshot_antes,
        snapshot_despues=_snapshot_colaborador(colaborador),
    )
    return colaborador


@transaction.atomic
def soft_delete_colaborador(*, colaborador: ColaboradorEspacioPWA, actor):
    if not colaborador.activo:
        raise ValidationError("El colaborador ya se encuentra inactivo.")
    snapshot_antes = _snapshot_colaborador(colaborador)
    colaborador.activo = False
    colaborador.fecha_baja = timezone.now()
    colaborador.actualizado_por = actor
    colaborador.save(
        update_fields=["activo", "fecha_baja", "actualizado_por", "fecha_actualizacion"]
    )
    registrar_evento_operacion(
        actor=actor,
        comedor_id=colaborador.comedor_id,
        entidad="colaborador",
        entidad_id=colaborador.id,
        accion="delete",
        snapshot_antes=snapshot_antes,
        snapshot_despues=_snapshot_colaborador(colaborador),
    )
    return colaborador
