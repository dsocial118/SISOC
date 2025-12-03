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

        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        api_key_header = request.META.get("HTTP_API_KEY", "")

        api_key = self._extract_api_key(auth_header, api_key_header)
        if api_key:
            return APIKey.objects.is_valid(api_key)

        return False

    def _extract_api_key(self, auth_header: str, api_key_header: str) -> str:
        """Obtiene el valor de la API Key desde los encabezados estándar.

        Prioriza el esquema `Authorization: Api-Key <API_KEY>` documentado en
        Swagger y mantiene compatibilidad con el header `API-KEY` usado
        previamente.
        """

        if auth_header:
            scheme, _, key = auth_header.partition(" ")
            if scheme.lower() == "api-key" and key.strip():
                return key.strip()

        return api_key_header.strip()
