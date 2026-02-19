from rest_framework.permissions import BasePermission

from users.services_pwa import is_pwa_user, is_representante


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
        comedor_id = view.kwargs.get("pk") or view.kwargs.get("comedor_id")
        if not comedor_id:
            return False
        try:
            comedor_id = int(comedor_id)
        except (TypeError, ValueError):
            return False
        return is_representante(user, comedor_id)
