from rest_framework.permissions import BasePermission

from iam.services import user_has_permission_code
from users.services_pwa import is_pwa_user, is_representante

MOBILE_RENDICION_PERMISSION_CODE = "rendicioncuentasmensual.manage_mobile_rendicion"


class IsPWAAuthenticatedToken(BasePermission):
    """Permite solo usuarios autenticados con acceso PWA activo."""

    message = "El usuario autenticado no tiene acceso PWA."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return is_pwa_user(user)


class IsPWARepresentativeForComedor(BasePermission):
    """Permite solo representantes activos del comedor de la URL."""

    message = "No tiene permisos de representante para este comedor."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        comedor_id = view.kwargs.get("comedor_id") or view.kwargs.get("pk")
        if not comedor_id:
            return False
        try:
            comedor_id = int(comedor_id)
        except (TypeError, ValueError):
            return False
        return is_representante(user, comedor_id)


class HasMobileRendicionPermission(BasePermission):
    """Permite solo usuarios con permiso explicito de rendición mobile."""

    message = "No tiene permiso para gestionar rendiciones en SISOC Mobile."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user_has_permission_code(user, MOBILE_RENDICION_PERMISSION_CODE)
