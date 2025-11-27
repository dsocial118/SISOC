from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
import logging

logger = logging.getLogger("django")


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

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {"error": "username y password son requeridos"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(username=username, password=password)

        if not user:
            logger.warning(f"Intento de login fallido para usuario: {username}")
            return Response(
                {"error": "Credenciales inválidas"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        token, created = Token.objects.get_or_create(user=user)
        
        logger.info(f"Token {'creado' if created else 'obtenido'} para usuario: {username}")
        
        return Response(
            {
                "token": token.key,
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
            },
            status=status.HTTP_200_OK,
        )
