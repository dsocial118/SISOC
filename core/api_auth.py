import logging

from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

logger = logging.getLogger("django")


class HasAPIKey(BasePermission):
    """
    Permite autenticación solo por APIKey (para GESCOM).
    """

    def has_permission(self, request, view):
        api_key = request.META.get("HTTP_X_API_KEY")
        if api_key:
            # Aquí iría la lógica para validar la APIKey
            return True
        return False


class HasAPIKeyOrToken(BasePermission):
    """
    Permite autenticación por APIKey (para GESCOM) o Token (para nuevas integraciones).
    """

    def has_permission(self, request, view):
        # Verificar Token (DRF TokenAuthentication)
        if request.user and request.user.is_authenticated:
            return True

        # Verificar APIKey en header
        api_key = request.META.get("HTTP_X_API_KEY")
        if api_key:
            return True

        return False


class IsInApiCentroFamiliaGroup(BasePermission):
    """
    Solo permite acceso a usuarios autenticados que pertenecen al grupo ApiCentroFamilia.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.groups.filter(name="ApiCentroFamilia").exists()


class LoginThrottle(AnonRateThrottle):
    scope = "login"
    rate = "5/min"


class ObtenerTokenView(APIView):
    """
    API para obtener token de autenticación.

    POST /api/token/
    Body: {
        "username": "admin",
        "password": "password123"
    }

    Respuesta:
    {
        "token": "abc123def456..."
    }
    """

    permission_classes = []
    authentication_classes = []
    throttle_classes = [LoginThrottle]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {"error": "username y password son requeridos"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(username) > 150 or len(password) > 128:
            return Response(
                {"error": "username o password inválidos"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(username=username, password=password)

        if not user:
            logger.warning("Intento de login fallido")
            return Response(
                {"error": "Credenciales inválidas"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        token, created = Token.objects.get_or_create(user=user)

        logger.info(
            f"Token {'creado' if created else 'obtenido'} para usuario: {user.id}"
        )

        return Response(
            {
                "token": token.key,
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
            },
            status=status.HTTP_200_OK,
        )
