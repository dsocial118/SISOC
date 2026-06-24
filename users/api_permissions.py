from rest_framework.permissions import BasePermission

from iam.services import user_has_permission_code
from users.services_pwa import has_pwa_access_to_comedor, is_pwa_user, is_representante

MOBILE_RENDICION_PERMISSION_CODE = "rendicioncuentasmensual.manage_mobile_rendicion"
PWA_PRESTACIONES_MENSUALES_PERMISSION_CODE = "pwa.manage_prestaciones_mensuales_pwa"
PWA_NOMINA_PERMISSION_CODE = "pwa.manage_nomina_pwa"
PWA_COLABORADORES_PERMISSION_CODE = "pwa.manage_colaboradores_pwa"
PWA_USUARIOS_PERMISSION_CODE = "pwa.manage_usuarios_pwa"


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


class IsPWAUserForComedor(BasePermission):
    """Permite usuarios PWA con acceso activo al comedor de la URL."""

    message = "No tiene acceso PWA para este comedor."

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
        return has_pwa_access_to_comedor(user, comedor_id)


class HasMobileRendicionPermission(BasePermission):
    """Permite solo usuarios con permiso explicito de rendición mobile."""

    message = "No tiene permiso para gestionar rendiciones en SISOC Mobile."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user_has_permission_code(user, MOBILE_RENDICION_PERMISSION_CODE)


class HasPwaPrestacionesMensualesPermission(BasePermission):
    """Permite operar la conformidad mensual de prestaciones PWA."""

    message = "No tiene permiso para gestionar prestaciones mensuales en SISOC Mobile."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user_has_permission_code(
            user, PWA_PRESTACIONES_MENSUALES_PERMISSION_CODE
        )


class HasPwaNominaPermission(BasePermission):
    """Permite operar altas, cambios y bajas de nomina PWA."""

    message = "No tiene permiso para gestionar nomina en SISOC Mobile."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user_has_permission_code(user, PWA_NOMINA_PERMISSION_CODE)


class HasPwaColaboradoresPermission(BasePermission):
    """Permite operar altas, cambios y bajas de colaboradores PWA."""

    message = "No tiene permiso para gestionar colaboradores en SISOC Mobile."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user_has_permission_code(user, PWA_COLABORADORES_PERMISSION_CODE)


class HasPwaUsuariosPermission(BasePermission):
    """Permite gestionar subusuarios PWA."""

    message = "No tiene permiso para gestionar usuarios en SISOC Mobile."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user_has_permission_code(user, PWA_USUARIOS_PERMISSION_CODE)
