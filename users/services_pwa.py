"""Servicios de dominio para accesos PWA."""

from __future__ import annotations

from datetime import timedelta
from typing import Iterable

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import F, Q
from django.utils import timezone

from users.models import AccesoComedorPWA, AuditAccesoComedorPWA, Profile
from users.profile_utils import get_profile_or_none

User = get_user_model()


def _registrar_auditoria_acceso(*, acceso, accion: str, actor=None, metadata=None):
    AuditAccesoComedorPWA.objects.create(
        acceso=acceso,
        user=getattr(acceso, "user", None),
        comedor=getattr(acceso, "comedor", None),
        organizacion=getattr(acceso, "organizacion", None),
        accion=accion,
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        metadata=metadata or {},
    )


def get_access_rows(user):
    """Retorna accesos PWA activos del usuario."""
    if not user or not getattr(user, "is_authenticated", False):
        return AccesoComedorPWA.objects.none()
    queryset = AccesoComedorPWA.objects.filter(
        user=user,
        activo=True,
    ).select_related("comedor", "creado_por", "organizacion")
    return queryset.filter(
        Q(tipo_asociacion=AccesoComedorPWA.TIPO_ASOCIACION_ESPACIO)
        | Q(
            tipo_asociacion=AccesoComedorPWA.TIPO_ASOCIACION_ORGANIZACION,
            organizacion_id=F("comedor__organizacion_id"),
        )
    )


def is_pwa_user(user) -> bool:
    """Indica si el usuario tiene al menos un acceso PWA activo."""
    return get_access_rows(user).exists()


def get_accessible_comedor_ids(user) -> list[int]:
    """IDs de comedores activos accesibles por el usuario."""
    return list(get_access_rows(user).values_list("comedor_id", flat=True))


def is_representante(user, comedor_id: int) -> bool:
    """Indica si el usuario es representante activo del comedor."""
    if not comedor_id:
        return False
    return (
        get_access_rows(user)
        .filter(
            comedor_id=comedor_id,
            rol=AccesoComedorPWA.ROL_REPRESENTANTE,
        )
        .exists()
    )


def get_pwa_context(user) -> dict:
    """Contexto resumido de accesos PWA para endpoint /me."""
    rows = get_access_rows(user)
    roles = sorted(set(rows.values_list("rol", flat=True)))
    representante_rows = rows.filter(rol=AccesoComedorPWA.ROL_REPRESENTANTE)
    comedores_representados = list(
        representante_rows.values_list("comedor_id", flat=True)
    )
    tipos_asociacion = sorted(
        {
            tipo
            for tipo in representante_rows.values_list("tipo_asociacion", flat=True)
            if tipo
        }
    )
    organizaciones_ids = list(
        representante_rows.exclude(organizacion_id__isnull=True)
        .values_list("organizacion_id", flat=True)
        .distinct()
    )
    comedor_operador_id = (
        rows.filter(rol=AccesoComedorPWA.ROL_OPERADOR)
        .values_list("comedor_id", flat=True)
        .first()
    )
    profile = get_profile_or_none(user)
    return {
        "is_pwa_user": bool(roles),
        "roles": roles,
        "comedores_representados": comedores_representados,
        "comedor_operador_id": comedor_operador_id,
        "tipo_asociacion": tipos_asociacion[0] if len(tipos_asociacion) == 1 else None,
        "organizaciones_ids": organizaciones_ids,
        "must_change_password": bool(getattr(profile, "must_change_password", False)),
    }


def _validate_operator_role_invariants(user):
    """Valida reglas de negocio para accesos operador activos."""
    active_rows = get_access_rows(user)
    active_roles = set(active_rows.values_list("rol", flat=True))
    has_operador = AccesoComedorPWA.ROL_OPERADOR in active_roles
    if not has_operador:
        return

    if AccesoComedorPWA.ROL_REPRESENTANTE in active_roles:
        raise ValidationError(
            "Un usuario PWA no puede tener roles activos representante y operador simultÃ¡neamente."
        )

    operadores = active_rows.filter(rol=AccesoComedorPWA.ROL_OPERADOR)
    if operadores.count() != 1:
        raise ValidationError(
            "Un usuario operador debe tener exactamente un acceso activo."
        )

    operador = operadores.first()
    if not operador.creado_por_id:
        raise ValidationError("Un usuario operador requiere usuario creador.")

    if not is_representante(operador.creado_por, operador.comedor_id):
        raise ValidationError(
            "El usuario creador debe ser representante activo del mismo comedor."
        )


@transaction.atomic
def create_operador_for_comedor(
    *,
    comedor_id: int,
    actor,
    username: str,
    email: str,
    password: str,
):
    """Crea usuario operador PWA en un comedor representado por actor."""
    if not is_representante(actor, comedor_id):
        raise PermissionDenied(
            "Solo representantes del comedor pueden crear operadores."
        )

    username = (username or "").strip()
    email = (email or "").strip()
    if not username:
        raise ValidationError({"username": "Este campo es obligatorio."})
    if not email:
        raise ValidationError({"email": "Este campo es obligatorio."})
    if not password:
        raise ValidationError({"password": "Este campo es obligatorio."})

    if User.objects.filter(username__iexact=username).exists():
        raise ValidationError({"username": "Ya existe un usuario con ese username."})
    if User.objects.filter(email__iexact=email).exists():
        raise ValidationError({"email": "Ya existe un usuario con ese email."})

    try:
        operador = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_staff=False,
            is_active=True,
        )
    except IntegrityError as exc:
        raise ValidationError(
            {"username": "Ya existe un usuario con ese username."}
        ) from exc
    operador.groups.clear()
    profile, _ = Profile.objects.get_or_create(user=operador)
    profile.must_change_password = True
    profile.password_changed_at = None
    profile.initial_password_expires_at = timezone.now() + timedelta(
        hours=settings.INITIAL_PASSWORD_MAX_AGE_HOURS
    )
    profile.save(
        update_fields=[
            "must_change_password",
            "password_changed_at",
            "initial_password_expires_at",
        ]
    )

    acceso = AccesoComedorPWA.objects.create(
        user=operador,
        comedor_id=comedor_id,
        rol=AccesoComedorPWA.ROL_OPERADOR,
        creado_por=actor,
        activo=True,
    )
    _registrar_auditoria_acceso(
        acceso=acceso,
        accion=AuditAccesoComedorPWA.ACCION_CREATE,
        actor=actor,
        metadata={"rol": AccesoComedorPWA.ROL_OPERADOR},
    )

    _validate_operator_role_invariants(operador)
    return acceso


def list_operadores_for_comedor(comedor_id: int):
    """Lista accesos de operadores activos para un comedor."""
    return (
        AccesoComedorPWA.objects.filter(
            comedor_id=comedor_id,
            rol=AccesoComedorPWA.ROL_OPERADOR,
            activo=True,
            user__is_active=True,
        )
        .select_related("user")
        .order_by("-fecha_creacion", "-id")
    )


@transaction.atomic
def deactivate_operador(*, comedor_id: int, user_id: int, actor):
    """Desactiva operador de un comedor y su usuario."""
    if not is_representante(actor, comedor_id):
        raise PermissionDenied(
            "Solo representantes del comedor pueden desactivar operadores."
        )

    acceso = (
        AccesoComedorPWA.objects.select_related("user")
        .filter(
            comedor_id=comedor_id,
            user_id=user_id,
            rol=AccesoComedorPWA.ROL_OPERADOR,
            activo=True,
        )
        .first()
    )
    if not acceso:
        raise ValidationError("El usuario no es un operador activo de este comedor.")

    now = timezone.now()
    accesos_activos = list(
        AccesoComedorPWA.objects.filter(user_id=user_id, activo=True)
    )
    AccesoComedorPWA.objects.filter(user_id=user_id, activo=True).update(
        activo=False,
        fecha_baja=now,
        fecha_actualizacion=now,
    )
    for acceso_activo in accesos_activos:
        acceso_activo.activo = False
        acceso_activo.fecha_baja = now
        _registrar_auditoria_acceso(
            acceso=acceso_activo,
            accion=AuditAccesoComedorPWA.ACCION_DEACTIVATE,
            actor=actor,
            metadata={"rol": acceso_activo.rol},
        )
    if acceso.user and acceso.user.is_active:
        acceso.user.is_active = False
        acceso.user.save(update_fields=["is_active"])

    return acceso


def _normalize_representante_access_specs(
    *,
    comedor_ids: Iterable[int] | None,
    access_specs: Iterable[dict] | None,
) -> list[dict]:
    if access_specs is None:
        return [
            {
                "comedor_id": int(comedor_id),
                "tipo_asociacion": AccesoComedorPWA.TIPO_ASOCIACION_ESPACIO,
                "organizacion_id": None,
            }
            for comedor_id in (comedor_ids or [])
        ]

    normalized_specs = []
    for spec in access_specs:
        comedor_id = int(spec["comedor_id"])
        tipo_asociacion = (
            spec.get("tipo_asociacion") or AccesoComedorPWA.TIPO_ASOCIACION_ESPACIO
        )
        organizacion_id = spec.get("organizacion_id")
        if tipo_asociacion not in {
            AccesoComedorPWA.TIPO_ASOCIACION_ORGANIZACION,
            AccesoComedorPWA.TIPO_ASOCIACION_ESPACIO,
        }:
            raise ValidationError("Tipo de asociaciÃ³n PWA invÃ¡lido.")
        if (
            tipo_asociacion == AccesoComedorPWA.TIPO_ASOCIACION_ORGANIZACION
            and not organizacion_id
        ):
            raise ValidationError(
                "Los accesos PWA asociados a organizaciÃ³n requieren una organizaciÃ³n."
            )
        if tipo_asociacion == AccesoComedorPWA.TIPO_ASOCIACION_ESPACIO:
            organizacion_id = None
        normalized_specs.append(
            {
                "comedor_id": comedor_id,
                "tipo_asociacion": tipo_asociacion,
                "organizacion_id": (
                    int(organizacion_id) if organizacion_id is not None else None
                ),
            }
        )
    return normalized_specs


def _get_representante_accesses_queryset(user):
    return AccesoComedorPWA.objects.filter(
        user=user,
        rol=AccesoComedorPWA.ROL_REPRESENTANTE,
        activo=True,
    )


@transaction.atomic
def sync_representante_accesses(
    *,
    user,
    comedor_ids: Iterable[int] | None = None,
    access_specs: Iterable[dict] | None = None,
    actor=None,
):
    """Sincroniza accesos representante activos con los comedores seleccionados."""
    normalized_specs = _normalize_representante_access_specs(
        comedor_ids=comedor_ids,
        access_specs=access_specs,
    )

    comedor_ids = {spec["comedor_id"] for spec in normalized_specs}
    if (
        comedor_ids
        and AccesoComedorPWA.objects.filter(
            user=user,
            rol=AccesoComedorPWA.ROL_OPERADOR,
            activo=True,
        ).exists()
    ):
        raise ValidationError(
            "No se puede asignar rol representante a un usuario con rol operador activo."
        )

    now = timezone.now()
    accesos_representante_activos = _get_representante_accesses_queryset(user)
    accesos_a_desactivar_qs = (
        accesos_representante_activos.exclude(comedor_id__in=comedor_ids)
        if comedor_ids
        else accesos_representante_activos
    )
    accesos_a_desactivar = list(accesos_a_desactivar_qs)
    accesos_a_desactivar_qs.update(
        activo=False,
        fecha_baja=now,
        fecha_actualizacion=now,
    )
    for acceso in accesos_a_desactivar:
        acceso.activo = False
        acceso.fecha_baja = now
        _registrar_auditoria_acceso(
            acceso=acceso,
            accion=AuditAccesoComedorPWA.ACCION_DEACTIVATE,
            actor=actor,
            metadata={"rol": acceso.rol},
        )

    existing_by_comedor = {
        row.comedor_id: row
        for row in AccesoComedorPWA.objects.filter(
            user=user,
            comedor_id__in=comedor_ids,
        )
    }
    for spec in normalized_specs:
        row = existing_by_comedor.get(spec["comedor_id"])
        if row:
            was_inactive = not row.activo
            changed = (
                was_inactive
                or row.rol != AccesoComedorPWA.ROL_REPRESENTANTE
                or row.tipo_asociacion != spec["tipo_asociacion"]
                or row.organizacion_id != spec["organizacion_id"]
            )
            row.rol = AccesoComedorPWA.ROL_REPRESENTANTE
            row.activo = True
            row.fecha_baja = None
            row.tipo_asociacion = spec["tipo_asociacion"]
            row.organizacion_id = spec["organizacion_id"]
            if not row.creado_por_id and actor:
                row.creado_por = actor
            row.save(
                update_fields=[
                    "rol",
                    "activo",
                    "fecha_baja",
                    "tipo_asociacion",
                    "organizacion",
                    "creado_por",
                    "fecha_actualizacion",
                ]
            )
            if changed:
                _registrar_auditoria_acceso(
                    acceso=row,
                    accion=(
                        AuditAccesoComedorPWA.ACCION_REACTIVATE
                        if was_inactive
                        else AuditAccesoComedorPWA.ACCION_CREATE
                    ),
                    actor=actor,
                    metadata={"rol": row.rol, "tipo_asociacion": row.tipo_asociacion},
                )
            continue

        acceso = AccesoComedorPWA.objects.create(
            user=user,
            comedor_id=spec["comedor_id"],
            organizacion_id=spec["organizacion_id"],
            rol=AccesoComedorPWA.ROL_REPRESENTANTE,
            tipo_asociacion=spec["tipo_asociacion"],
            creado_por=actor if actor and actor != user else None,
            activo=True,
        )
        _registrar_auditoria_acceso(
            acceso=acceso,
            accion=AuditAccesoComedorPWA.ACCION_CREATE,
            actor=actor,
            metadata={"rol": acceso.rol, "tipo_asociacion": acceso.tipo_asociacion},
        )


@transaction.atomic
def deactivate_representante_accesses(user):
    """Desactiva accesos representante activos del usuario."""
    accesos = list(
        AccesoComedorPWA.objects.filter(
            user=user,
            rol=AccesoComedorPWA.ROL_REPRESENTANTE,
            activo=True,
        )
    )
    now = timezone.now()
    AccesoComedorPWA.objects.filter(
        user=user,
        rol=AccesoComedorPWA.ROL_REPRESENTANTE,
        activo=True,
    ).update(
        activo=False,
        fecha_baja=now,
        fecha_actualizacion=now,
    )
    for acceso in accesos:
        acceso.activo = False
        acceso.fecha_baja = now
        _registrar_auditoria_acceso(
            acceso=acceso,
            accion=AuditAccesoComedorPWA.ACCION_DEACTIVATE,
            metadata={"rol": acceso.rol},
        )
