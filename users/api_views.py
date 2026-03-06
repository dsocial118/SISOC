from drf_spectacular.utils import extend_schema
from django.contrib.auth import authenticate
from django.core.exceptions import PermissionDenied
from rest_framework import serializers, status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from pwa.models import AuditoriaSesionPWA
from pwa.services.auditoria_service import registrar_evento_auth
from users.api_serializers import UserContextSerializer
from users.services_pwa import is_pwa_user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def _raise_read_only(self):
        raise NotImplementedError("Serializer de solo lectura.")

    def create(self, validated_data):
        return self._raise_read_only()

    def update(self, instance, validated_data):
        return self._raise_read_only()

    def validate(self, attrs):
        user = authenticate(
            username=attrs.get("username"), password=attrs.get("password")
        )
        if not user or not user.is_active:
            raise AuthenticationFailed("Credenciales inválidas.")
        attrs["user"] = user
        return attrs


@extend_schema(tags=["Auth"])
class UserLoginViewSet(viewsets.ViewSet):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(request=LoginSerializer)
    def create(self, request):
        serializer = LoginSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except (AuthenticationFailed, PermissionDenied) as exc:
            detail = (
                str(exc)
                if isinstance(exc, AuthenticationFailed)
                else "Credenciales inválidas."
            )
            response = Response(
                {"detail": detail},
                status=status.HTTP_401_UNAUTHORIZED,
            )
            registrar_evento_auth(
                request=request,
                evento=AuditoriaSesionPWA.EVENTO_LOGIN_ERROR,
                resultado=AuditoriaSesionPWA.RESULTADO_ERROR,
                username_intentado=request.data.get("username"),
                codigo_respuesta=response.status_code,
                motivo_error=detail,
            )
            return response
        user = serializer.validated_data["user"]
        if not is_pwa_user(user):
            detail = "Este usuario no tiene acceso PWA activo."
            response = Response(
                {"detail": detail},
                status=status.HTTP_401_UNAUTHORIZED,
            )
            registrar_evento_auth(
                request=request,
                evento=AuditoriaSesionPWA.EVENTO_LOGIN_ERROR,
                resultado=AuditoriaSesionPWA.RESULTADO_ERROR,
                user=user,
                username_intentado=request.data.get("username"),
                codigo_respuesta=response.status_code,
                motivo_error=detail,
            )
            return response

        token, _ = Token.objects.get_or_create(user=user)
        response = Response(
            {
                "token": token.key,
                "token_type": "Token",
                "user_id": user.id,
                "username": user.username,
            },
            status=status.HTTP_200_OK,
        )
        registrar_evento_auth(
            request=request,
            evento=AuditoriaSesionPWA.EVENTO_LOGIN_OK,
            resultado=AuditoriaSesionPWA.RESULTADO_OK,
            user=user,
            username_intentado=request.data.get("username"),
            codigo_respuesta=response.status_code,
        )
        return response


@extend_schema(tags=["Auth"])
class UserLogoutViewSet(viewsets.ViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None)
    def create(self, request):
        token = getattr(request, "auth", None)
        if isinstance(token, Token):
            token.delete()
        else:
            Token.objects.filter(user=request.user).delete()
        response = Response({"detail": "Logout exitoso."}, status=status.HTTP_200_OK)
        registrar_evento_auth(
            request=request,
            evento=AuditoriaSesionPWA.EVENTO_LOGOUT,
            resultado=AuditoriaSesionPWA.RESULTADO_OK,
            user=request.user,
            codigo_respuesta=response.status_code,
        )
        return response


@extend_schema(tags=["Auth"])
class UserContextViewSet(viewsets.ViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=UserContextSerializer)
    def list(self, request):
        serializer = UserContextSerializer(request.user)
        response = Response(serializer.data, status=status.HTTP_200_OK)
        registrar_evento_auth(
            request=request,
            evento=AuditoriaSesionPWA.EVENTO_ME_OK,
            resultado=AuditoriaSesionPWA.RESULTADO_OK,
            user=request.user,
            codigo_respuesta=response.status_code,
        )
        return response
