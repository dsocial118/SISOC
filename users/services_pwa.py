"""Servicios de dominio para accesos PWA."""

from __future__ import annotations

from typing import Iterable

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from users.models import AccesoComedorPWA

User = get_user_model()


def get_access_rows(user):
    """Retorna accesos PWA activos del usuario."""
    if not user or not getattr(user, "is_authenticated", False):
        return AccesoComedorPWA.objects.none()
    return AccesoComedorPWA.objects.filter(
        user=user,
        activo=True,
    ).select_related("comedor", "creado_por")


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
    comedores_representados = list(
        rows.filter(rol=AccesoComedorPWA.ROL_REPRESENTANTE).values_list(
            "comedor_id", flat=True
        )
    )
    comedor_operador_id = (
        rows.filter(rol=AccesoComedorPWA.ROL_OPERADOR)
        .values_list("comedor_id", flat=True)
        .first()
    )
    return {
        "is_pwa_user": bool(roles),
        "roles": roles,
        "comedores_representados": comedores_representados,
        "comedor_operador_id": comedor_operador_id,
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
            "Un usuario PWA no puede tener roles activos representante y operador simultáneamente."
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

    acceso = AccesoComedorPWA.objects.create(
        user=operador,
        comedor_id=comedor_id,
        rol=AccesoComedorPWA.ROL_OPERADOR,
        creado_por=actor,
        activo=True,
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
    AccesoComedorPWA.objects.filter(user_id=user_id, activo=True).update(
        activo=False,
        fecha_actualizacion=now,
    )
    if acceso.user and acceso.user.is_active:
        acceso.user.is_active = False
        acceso.user.save(update_fields=["is_active"])

    return acceso


@transaction.atomic
def sync_representante_accesses(
    *,
    user,
    comedor_ids: Iterable[int],
    actor=None,
):
    """Sincroniza accesos representante activos con los comedores seleccionados."""
    comedor_ids = {int(comedor_id) for comedor_id in comedor_ids}
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
    if comedor_ids:
        AccesoComedorPWA.objects.filter(
            user=user,
            rol=AccesoComedorPWA.ROL_REPRESENTANTE,
            activo=True,
        ).exclude(comedor_id__in=comedor_ids).update(
            activo=False,
            fecha_actualizacion=now,
        )
    else:
        AccesoComedorPWA.objects.filter(
            user=user,
            rol=AccesoComedorPWA.ROL_REPRESENTANTE,
            activo=True,
        ).update(
            activo=False,
            fecha_actualizacion=now,
        )

    existing_by_comedor = {
        row.comedor_id: row
        for row in AccesoComedorPWA.objects.filter(
            user=user,
            comedor_id__in=comedor_ids,
        )
    }
    for comedor_id in comedor_ids:
        row = existing_by_comedor.get(comedor_id)
        if row:
            row.rol = AccesoComedorPWA.ROL_REPRESENTANTE
            row.activo = True
            if not row.creado_por_id and actor:
                row.creado_por = actor
            row.save(
                update_fields=["rol", "activo", "creado_por", "fecha_actualizacion"]
            )
            continue

        AccesoComedorPWA.objects.create(
            user=user,
            comedor_id=comedor_id,
            rol=AccesoComedorPWA.ROL_REPRESENTANTE,
            creado_por=actor if actor and actor != user else None,
            activo=True,
        )


@transaction.atomic
def deactivate_representante_accesses(user):
    """Desactiva accesos representante activos del usuario."""
    AccesoComedorPWA.objects.filter(
        user=user,
        rol=AccesoComedorPWA.ROL_REPRESENTANTE,
        activo=True,
    ).update(
        activo=False,
        fecha_actualizacion=timezone.now(),
    )
