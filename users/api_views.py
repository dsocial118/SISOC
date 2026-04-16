import logging

from drf_spectacular.utils import extend_schema
from django.contrib.auth import authenticate
from django.core.exceptions import PermissionDenied
from django.db import transaction
from rest_framework import serializers, status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from pwa.models import AuditoriaSesionPWA
from pwa.services.auditoria_service import registrar_evento_auth
from users.api_serializers import (
    PasswordChangeRequiredSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    UserContextSerializer,
)
from users.rate_limits import hit_rate_limit
from users.profile_utils import get_profile_or_none
from users.services_auth import (
    change_password_for_authenticated_user,
    confirm_password_reset,
    request_password_reset_for_email,
    request_password_reset_for_username,
)
from users.services_pwa import get_access_rows, is_pwa_user

logger = logging.getLogger("django")


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
        try:
            serializer = UserContextSerializer(request.user)
            payload = serializer.data
        except (
            Exception
        ):  # pragma: no cover - fallback defensivo para no cortar login PWA
            logger.exception(
                "Fallo serializando /api/users/me/ para user_id=%s",
                getattr(request.user, "id", None),
            )
            profile = get_profile_or_none(request.user)
            try:
                roles = sorted(
                    set(get_access_rows(request.user).values_list("rol", flat=True))
                )
            except Exception:  # pragma: no cover - fallback ultra defensivo
                roles = []
            payload = {
                "id": getattr(request.user, "id", None),
                "username": getattr(request.user, "username", ""),
                "email": getattr(request.user, "email", ""),
                "first_name": getattr(request.user, "first_name", ""),
                "last_name": getattr(request.user, "last_name", ""),
                "pwa": {
                    "roles": roles,
                    "must_change_password": bool(
                        getattr(profile, "must_change_password", False)
                    ),
                },
                "permissions": [],
            }
        response = Response(payload, status=status.HTTP_200_OK)
        registrar_evento_auth(
            request=request,
            evento=AuditoriaSesionPWA.EVENTO_ME_OK,
            resultado=AuditoriaSesionPWA.RESULTADO_OK,
            user=request.user,
            codigo_respuesta=response.status_code,
        )
        return response


@extend_schema(tags=["Auth"])
class PasswordResetRequestViewSet(viewsets.ViewSet):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(request=PasswordResetRequestSerializer)
    def create(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ip = request.META.get("REMOTE_ADDR", "anon")
        email = serializer.validated_data.get("email")
        username = serializer.validated_data.get("username")
        identity_value = (email or username or "").lower()
        if hit_rate_limit(
            scope="password_reset_request",
            identity=f"{ip}:{identity_value}",
            limit=5,
            window_seconds=900,
        ):
            return Response(
                {
                    "detail": (
                        "Demasiados intentos. Intente nuevamente en unos minutos."
                    )
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        if email:
            request_password_reset_for_email(email=email, request=request)
        elif username:
            request_password_reset_for_username(username=username)
        return Response(
            {
                "detail": (
                    "Si el usuario existe en el sistema, se registró la solicitud de reseteo."
                )
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=["Auth"])
class PasswordResetConfirmViewSet(viewsets.ViewSet):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(request=PasswordResetConfirmSerializer)
    @transaction.atomic
    def create(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ip = request.META.get("REMOTE_ADDR", "anon")
        if hit_rate_limit(
            scope="password_reset_confirm",
            identity=ip,
            limit=10,
            window_seconds=900,
        ):
            return Response(
                {
                    "detail": (
                        "Demasiados intentos. Intente nuevamente en unos minutos."
                    )
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        user = confirm_password_reset(
            uid=serializer.validated_data["uid"],
            token=serializer.validated_data["token"],
            new_password=serializer.validated_data["new_password"],
        )
        if not user:
            return Response(
                {"detail": "Token inválido o expirado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        Token.objects.filter(user=user).delete()
        return Response(
            {"detail": "Contraseña actualizada correctamente."},
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=["Auth"])
class PasswordChangeRequiredViewSet(viewsets.ViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(request=PasswordChangeRequiredSerializer)
    @transaction.atomic
    def create(self, request):
        serializer = PasswordChangeRequiredSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        profile = getattr(request.user, "profile", None)
        if not getattr(profile, "must_change_password", False):
            return Response(
                {"detail": "El usuario no requiere cambio obligatorio de contraseña."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        change_password_for_authenticated_user(
            user=request.user,
            new_password=serializer.validated_data["new_password"],
        )
        return Response(
            {"detail": "Contraseña actualizada correctamente."},
            status=status.HTTP_200_OK,
        )
