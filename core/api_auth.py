from rest_framework.permissions import BasePermission
from rest_framework_api_key.models import APIKey
from rest_framework_api_key.permissions import HasAPIKey

__all__ = ["HasAPIKey", "HasAPIKeyOrToken"]


class HasAPIKeyOrToken(BasePermission):
    """
    Permite autenticación por APIKey (para GESCOM/relevamientos) o Token.
    """

    def has_permission(self, request, view):
        # Verificar Token (DRF TokenAuthentication)
        if request.user and request.user.is_authenticated:
            return True

        if HasAPIKey().has_permission(request, view):
            return True

        # Compatibilidad con integraciones legadas que envían `API-KEY`.
        legacy_api_key = request.META.get("HTTP_API_KEY", "").strip()
        if legacy_api_key:
            return APIKey.objects.is_valid(legacy_api_key)

        return False
