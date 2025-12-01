from rest_framework_api_key.models import APIKey
from rest_framework_api_key.permissions import HasAPIKey
from rest_framework.permissions import BasePermission

__all__ = ["HasAPIKey", "HasAPIKeyOrToken"]


class HasAPIKeyOrToken(BasePermission):
    """
    Permite autenticación por APIKey (para GESCOM/relevamientos) o Token.
    """

    def has_permission(self, request, view):
        # Verificar Token (DRF TokenAuthentication)
        if request.user and request.user.is_authenticated:
            return True

        # Verificar APIKey en header
        api_key = request.META.get("HTTP_API_KEY")
        if api_key:
            return APIKey.objects.is_valid(api_key)

        return False
