"""
Módulo centralizado para validaciones de permisos en celiaquia.
"""

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from celiaquia.models import RevisionTecnico
from iam.services import user_has_permission_code

ROLE_COORDINADOR_PERMISSION = "auth.role_coordinadorceliaquia"
ROLE_TECNICO_PERMISSION = "auth.role_tecnicoceliaquia"
ROLE_PROVINCIA_PERMISSION = "auth.role_provinciaceliaquia"


def _has_permission(user, permission_code: str) -> bool:
    return user_has_permission_code(user, permission_code)


def _safe_profile(user):
    """Retorna el perfil del usuario o None si no existe."""
    if not user:
        return None
    try:
        return user.profile
    except ObjectDoesNotExist:
        return None


def can_edit_legajo_files(user, expediente, legajo=None):
    """
    Verifica si el usuario puede editar archivos de legajo.

    Args:
        user: Usuario actual
        expediente: Expediente al que pertenece el legajo
        legajo: Legajo específico (opcional)

    Returns:
        bool: True si puede editar, False en caso contrario

    Raises:
        PermissionDenied: Si no tiene permisos
    """
    if not user.is_authenticated:
        raise PermissionDenied("Autenticación requerida.")

    is_admin = user.is_superuser
    is_coord = _has_permission(user, ROLE_COORDINADOR_PERMISSION)
    is_tec = _has_permission(user, ROLE_TECNICO_PERMISSION)
    is_prov = _has_permission(user, ROLE_PROVINCIA_PERMISSION)

    if not (is_admin or is_coord or is_tec or is_prov):
        raise PermissionDenied("Permiso denegado.")

    # Provincia: validaciones específicas
    if is_prov and not (is_admin or is_coord):
        # Verificar misma provincia
        owner = getattr(expediente, "usuario_provincia", None)
        up = _safe_profile(user)
        op = _safe_profile(owner) if owner else None
        if (
            not owner
            or not up
            or not op
            or getattr(up, "provincia_id", None) != getattr(op, "provincia_id", None)
        ):
            raise PermissionDenied("No pertenece a la misma provincia del expediente.")

        # Verificar estados permitidos
        estado_nombre = getattr(getattr(expediente, "estado", None), "nombre", "")
        legajo_subsanar = legajo and legajo.revision_tecnico == RevisionTecnico.SUBSANAR

        if not (estado_nombre == "EN_ESPERA" or legajo_subsanar):
            raise PermissionDenied("No puede editar archivos en el estado actual.")

    # Técnico: debe estar asignado
    if is_tec and not (is_admin or is_coord):
        if not expediente.asignaciones_tecnicos.filter(tecnico=user).exists():
            raise PermissionDenied("No sos el técnico asignado a este expediente.")

    return True


def can_review_legajo(user, expediente):
    """
    Verifica si el usuario puede revisar legajos (aprobar/rechazar/subsanar).
    """
    if not user.is_authenticated:
        raise PermissionDenied("Autenticación requerida.")

    is_admin = user.is_superuser
    is_coord = _has_permission(user, ROLE_COORDINADOR_PERMISSION)
    is_tec = _has_permission(user, ROLE_TECNICO_PERMISSION)

    if not (is_admin or is_coord or is_tec):
        raise PermissionDenied("Permiso denegado.")

    # Técnico: debe estar asignado
    if is_tec and not (is_admin or is_coord):
        if not expediente.asignaciones_tecnicos.filter(tecnico=user).exists():
            raise PermissionDenied("No sos el técnico asignado a este expediente.")

    return True


def can_confirm_subsanacion(user, expediente):
    """
    Verifica si el usuario puede confirmar subsanación.
    """
    if not user.is_authenticated:
        raise PermissionDenied("Autenticación requerida.")

    is_admin = user.is_superuser
    is_prov = _has_permission(user, ROLE_PROVINCIA_PERMISSION)

    if not (is_admin or is_prov):
        raise PermissionDenied(
            "No tenés permiso para confirmar la subsanación de este expediente."
        )

    # Verificar que pertenezca a la misma provincia
    if is_prov and not is_admin:
        owner = getattr(expediente, "usuario_provincia", None)
        up = _safe_profile(user)
        op = _safe_profile(owner) if owner else None
        if (
            not owner
            or not up
            or not op
            or getattr(up, "provincia_id", None) != getattr(op, "provincia_id", None)
        ):
            raise PermissionDenied(
                "No tenés permiso para confirmar la subsanación de este expediente."
            )

    return True
