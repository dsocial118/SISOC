"""Servicios de dominio para accesos PWA."""

from __future__ import annotations

from datetime import timedelta
from typing import Iterable

from django.conf import settings
from django.contrib.auth import password_validation
from django.contrib.auth.models import Permission
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import F, Q
from django.utils import timezone

from comedores.models import Comedor
from comedores.services.capacitaciones_certificados_service import (
    is_alimentar_comunidad_program,
)
from users.models import AccesoComedorPWA, AuditAccesoComedorPWA, Profile
from users.profile_utils import get_profile_or_none
from iam.services import get_effective_permission_codes

User = get_user_model()

PWA_USUARIOS_PERMISSION_CODE = "pwa.manage_usuarios_pwa"
MOBILE_RENDICION_PERMISSION_CODE = "rendicioncuentasmensual.manage_mobile_rendicion"
PWA_ASSIGNABLE_PERMISSION_CODES = {
    MOBILE_RENDICION_PERMISSION_CODE,
    "pwa.manage_prestaciones_mensuales_pwa",
    "pwa.manage_nomina_pwa",
    "pwa.manage_colaboradores_pwa",
}


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


def _get_effective_mobile_permission_codes(user) -> list[str]:
    return sorted(
        code
        for code in get_effective_permission_codes(user)
        if code in PWA_ASSIGNABLE_PERMISSION_CODES
        or code == PWA_USUARIOS_PERMISSION_CODE
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


def has_pwa_access_to_comedor(user, comedor_id: int) -> bool:
    """Indica si el usuario tiene acceso PWA activo al comedor."""
    if not comedor_id:
        return False
    return get_access_rows(user).filter(comedor_id=comedor_id).exists()


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
            "Un usuario PWA no puede tener roles activos representante y operador simultáneamente."
        )

    operadores = list(active_rows.filter(rol=AccesoComedorPWA.ROL_OPERADOR))
    if not operadores:
        raise ValidationError(
            "Un usuario operador debe tener al menos un acceso activo."
        )

    for operador in operadores:
        if not operador.creado_por_id:
            raise ValidationError("Un usuario operador requiere usuario creador.")

        if not is_representante(operador.creado_por, operador.comedor_id):
            raise ValidationError(
                "El usuario creador debe ser representante activo del mismo comedor."
            )


def _resolve_permission_codes(permission_codes: Iterable[str]) -> list[Permission]:
    permissions = []
    for code in permission_codes:
        try:
            app_label, codename = str(code).split(".", 1)
        except ValueError as exc:
            raise ValidationError({"permission_codes": "Permiso invalido."}) from exc
        permission = Permission.objects.filter(
            content_type__app_label=app_label,
            codename=codename,
        ).first()
        if not permission:
            raise ValidationError({"permission_codes": f"Permiso inexistente: {code}."})
        permissions.append(permission)
    return permissions


def _is_alimentar_comunidad_comedor(comedor_id: int | None) -> bool:
    if not comedor_id:
        return False
    comedor = Comedor.objects.select_related("programa").filter(pk=comedor_id).first()
    return bool(comedor and is_alimentar_comunidad_program(comedor))


def _filter_permission_codes_for_comedor_context(
    permission_codes: Iterable[str],
    comedor_id: int | None,
) -> list[str]:
    codes = {str(code).strip() for code in permission_codes or [] if str(code).strip()}
    if _is_alimentar_comunidad_comedor(comedor_id):
        codes.discard(MOBILE_RENDICION_PERMISSION_CODE)
    return sorted(codes)


def get_assignable_pwa_permission_codes(
    actor, comedor_id: int | None = None
) -> list[str]:
    actor_codes = set(get_effective_permission_codes(actor))
    actor_codes.discard(PWA_USUARIOS_PERMISSION_CODE)
    return _filter_permission_codes_for_comedor_context(
        actor_codes & PWA_ASSIGNABLE_PERMISSION_CODES,
        comedor_id,
    )


def _validate_assignable_permissions(
    actor, permission_codes: Iterable[str], comedor_id: int | None = None
) -> list[str]:
    requested_codes = {
        str(code).strip() for code in permission_codes or [] if str(code).strip()
    }
    allowed_codes = set(get_assignable_pwa_permission_codes(actor, comedor_id))
    requested_codes = set(
        _filter_permission_codes_for_comedor_context(requested_codes, comedor_id)
    )
    denied_codes = sorted(requested_codes - allowed_codes)
    if denied_codes:
        raise ValidationError(
            {
                "permission_codes": (
                    "No puede asignar permisos que no posee: "
                    f"{', '.join(denied_codes)}."
                )
            }
        )
    return sorted(requested_codes)


def _validate_assignable_comedores(actor, comedor_ids: Iterable[int]) -> list[int]:
    try:
        requested_ids = sorted({int(comedor_id) for comedor_id in comedor_ids})
    except (TypeError, ValueError) as exc:
        raise ValidationError({"comedor_ids": "Espacio invalido."}) from exc
    if not requested_ids:
        raise ValidationError({"comedor_ids": "Debe asignar al menos un espacio."})
    allowed_ids = set(get_accessible_comedor_ids(actor))
    denied_ids = sorted(set(requested_ids) - allowed_ids)
    if denied_ids:
        raise PermissionDenied(
            "No puede asignar espacios fuera de su alcance PWA: "
            f"{', '.join(map(str, denied_ids))}."
        )
    for requested_id in requested_ids:
        if not is_representante(actor, requested_id):
            raise PermissionDenied(
                "Solo representantes del comedor pueden crear operadores."
            )
    return requested_ids


@transaction.atomic
# pylint: disable-next=too-many-arguments,too-many-locals
def create_operador_for_comedor(
    *,
    comedor_id: int,
    actor,
    username: str,
    email: str,
    password: str,
    comedor_ids: Iterable[int] | None = None,
    permission_codes: Iterable[str] | None = None,
):
    """Crea usuario operador PWA en un comedor representado por actor."""
    requested_comedor_ids = _validate_assignable_comedores(
        actor,
        comedor_ids or [comedor_id],
    )
    requested_permission_codes = _validate_assignable_permissions(
        actor,
        permission_codes or [],
        comedor_id,
    )

    username = (username or "").strip()
    email = (email or "").strip()
    if not username:
        raise ValidationError({"username": "Este campo es obligatorio."})
    if not password:
        raise ValidationError({"password": "Este campo es obligatorio."})
    password_user = User(username=username, email=email)
    try:
        password_validation.validate_password(password, user=password_user)
    except ValidationError as exc:
        raise ValidationError({"password": list(exc.messages)}) from exc

    if User.objects.filter(username__iexact=username).exists():
        raise ValidationError({"username": "Ya existe un usuario con ese username."})

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
    operador.user_permissions.set(_resolve_permission_codes(requested_permission_codes))
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

    created_accesses = []
    for target_comedor_id in requested_comedor_ids:
        acceso = AccesoComedorPWA.objects.create(
            user=operador,
            comedor_id=target_comedor_id,
            rol=AccesoComedorPWA.ROL_OPERADOR,
            creado_por=actor,
            activo=True,
        )
        created_accesses.append(acceso)
        _registrar_auditoria_acceso(
            acceso=acceso,
            accion=AuditAccesoComedorPWA.ACCION_CREATE,
            actor=actor,
            metadata={
                "rol": AccesoComedorPWA.ROL_OPERADOR,
                "permission_codes": requested_permission_codes,
            },
        )

    _validate_operator_role_invariants(operador)
    return created_accesses[0]


def list_operadores_for_comedor(comedor_id: int):
    """Lista accesos de operadores activos para un comedor."""
    return (
        AccesoComedorPWA.objects.filter(
            comedor_id=comedor_id,
            rol=AccesoComedorPWA.ROL_OPERADOR,
            activo=True,
            user__is_active=True,
        )
        .select_related("user", "creado_por")
        .prefetch_related("user__user_permissions__content_type")
        .order_by("-fecha_creacion", "-id")
    )


@transaction.atomic
def update_operador_permissions(
    *,
    comedor_id: int,
    user_id: int,
    actor,
    permission_codes: Iterable[str] | None = None,
):
    """Actualiza permisos delegados de un operador creado por el representante."""
    if not is_representante(actor, comedor_id):
        raise PermissionDenied(
            "Solo representantes del comedor pueden editar operadores."
        )

    acceso = (
        AccesoComedorPWA.objects.select_related("user", "creado_por")
        .filter(
            comedor_id=comedor_id,
            user_id=user_id,
            rol=AccesoComedorPWA.ROL_OPERADOR,
            activo=True,
            user__is_active=True,
        )
        .first()
    )
    if not acceso:
        raise PermissionDenied("No tiene acceso para editar este operador.")
    if acceso.creado_por_id != getattr(actor, "id", None):
        raise PermissionDenied("Solo puede editar usuarios creados por usted.")

    requested_permission_codes = _validate_assignable_permissions(
        actor,
        permission_codes or [],
        comedor_id,
    )
    previous_permission_codes = _get_effective_mobile_permission_codes(acceso.user)
    acceso.user.user_permissions.set(
        _resolve_permission_codes(requested_permission_codes)
    )
    _registrar_auditoria_acceso(
        acceso=acceso,
        accion=AuditAccesoComedorPWA.ACCION_UPDATE_PERMISSIONS,
        actor=actor,
        metadata={
            "rol": AccesoComedorPWA.ROL_OPERADOR,
            "previous_permission_codes": previous_permission_codes,
            "new_permission_codes": requested_permission_codes,
        },
    )
    return acceso


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
    allowed_comedor_ids = set(get_accessible_comedor_ids(actor))
    denied_comedor_ids = sorted(
        {
            acceso_activo.comedor_id
            for acceso_activo in accesos_activos
            if acceso_activo.comedor_id not in allowed_comedor_ids
        }
    )
    if denied_comedor_ids:
        raise PermissionDenied(
            "No puede desactivar accesos fuera de su alcance PWA: "
            f"{', '.join(map(str, denied_comedor_ids))}."
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
            raise ValidationError("Tipo de asociación PWA inválido.")
        if (
            tipo_asociacion == AccesoComedorPWA.TIPO_ASOCIACION_ORGANIZACION
            and not organizacion_id
        ):
            raise ValidationError(
                "Los accesos PWA asociados a organización requieren una organización."
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
