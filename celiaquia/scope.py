"""Reglas de visibilidad de expedientes de Celiaquia.

Vivian como helpers privados de `celiaquia/views/expediente.py`. Se extraen aca
para que la API REST aplique **exactamente** el mismo alcance que las pantallas:
duplicar estas reglas es la forma mas facil de filtrar datos de otra provincia.

La vista sigue siendo la unica consumidora del resto de su logica; de aca solo
salen las funciones que deciden "que expedientes puede ver este usuario".
"""

from __future__ import annotations

from django.db.models import Q, QuerySet

from iam.services import user_has_permission_code
from users.territorial_scope import (
    build_territorial_scope_q,
    get_effective_scopes,
    is_territorial_user,
)

ROLE_COORDINADOR_CELIAQUIA_PERMISSION = "auth.role_coordinadorceliaquia"
ROLE_TECNICO_CELIAQUIA_PERMISSION = "auth.role_tecnicoceliaquia"
ROLE_PROVINCIA_CELIAQUIA_PERMISSION = "auth.role_provinciaceliaquia"


def user_has_permission(user, permission_code: str) -> bool:
    return user_has_permission_code(user, permission_code)


def is_admin(user) -> bool:
    return bool(
        getattr(user, "is_authenticated", False)
        and getattr(user, "is_superuser", False)
    )


def is_provincial(user) -> bool:
    from django.core.exceptions import ObjectDoesNotExist

    try:
        if is_territorial_user(user):
            return True
        return user_has_permission(user, ROLE_PROVINCIA_CELIAQUIA_PERMISSION)
    except ObjectDoesNotExist:
        return False


def is_coordinador(user) -> bool:
    return user_has_permission(user, ROLE_COORDINADOR_CELIAQUIA_PERMISSION)


def is_tecnico(user) -> bool:
    return user_has_permission(user, ROLE_TECNICO_CELIAQUIA_PERMISSION)


def apply_provincial_expediente_scope(queryset: QuerySet, user) -> QuerySet:
    """Expedientes visibles para un usuario provincial/territorial."""

    if getattr(user, "is_superuser", False):
        return queryset
    if not is_territorial_user(user):
        # Tiene role_provinciaceliaquia pero no scope territorial configurado;
        # restringir a expedientes propios.
        return queryset.filter(usuario_provincia=user).distinct()

    # Un expediente es visible si tiene al menos un ciudadano dentro del alcance
    # territorial del usuario. NO se incluyen los expedientes propios fuera de
    # alcance (sin include_own): un expediente cargado por el usuario con
    # ciudadanos de otra provincia no debe listarse (seguimiento del issue #1793).
    scope_q = build_territorial_scope_q(
        get_effective_scopes(user),
        provincia_lookup="expediente_ciudadanos__ciudadano__provincia_id",
        municipio_lookup="expediente_ciudadanos__ciudadano__municipio_id",
        localidad_lookup="expediente_ciudadanos__ciudadano__localidad_id",
    )
    # Excepcion: sus propios expedientes recien creados, aun sin legajos
    # importados (sin provincia derivable todavia), deben seguir siendo accesibles
    # para poder cargar/procesar el Excel.
    propios_sin_legajos_q = Q(
        usuario_provincia=user, expediente_ciudadanos__isnull=True
    )
    combined_q = (
        propios_sin_legajos_q if scope_q is None else scope_q | propios_sin_legajos_q
    )
    return queryset.filter(combined_q).distinct()


def scope_expedientes(queryset: QuerySet, user) -> QuerySet:
    """Alcance completo por rol, en el mismo orden de precedencia que el listado.

    admin y coordinador ven todo; el provincial, su territorio; el tecnico, los
    expedientes que tiene asignados; cualquier otro, solo los que creo.
    """

    if is_admin(user):
        return queryset
    if is_provincial(user):
        return apply_provincial_expediente_scope(queryset, user)
    if is_coordinador(user):
        return queryset
    if is_tecnico(user):
        return queryset.filter(asignaciones_tecnicos__tecnico=user).distinct()
    return queryset.filter(usuario_provincia=user)


__all__ = [
    "ROLE_COORDINADOR_CELIAQUIA_PERMISSION",
    "ROLE_TECNICO_CELIAQUIA_PERMISSION",
    "ROLE_PROVINCIA_CELIAQUIA_PERMISSION",
    "apply_provincial_expediente_scope",
    "is_admin",
    "is_coordinador",
    "is_provincial",
    "is_tecnico",
    "scope_expedientes",
    "user_has_permission",
]
