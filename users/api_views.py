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

from users.api_serializers import (
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    UserContextSerializer,
)
from users.rate_limits import hit_rate_limit
from users.services_auth import confirm_password_reset, request_password_reset_for_email


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
            return Response(
                {"detail": detail},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                "token": token.key,
                "token_type": "Token",
                "user_id": user.id,
                "username": user.username,
            },
            status=status.HTTP_200_OK,
        )


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
        return Response({"detail": "Logout exitoso."}, status=status.HTTP_200_OK)


@extend_schema(tags=["Auth"])
class UserContextViewSet(viewsets.ViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=UserContextSerializer)
    def list(self, request):
        serializer = UserContextSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(tags=["Auth"])
class PasswordResetRequestViewSet(viewsets.ViewSet):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(request=PasswordResetRequestSerializer)
    def create(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ip = request.META.get("REMOTE_ADDR", "anon")
        email = serializer.validated_data["email"].lower()
        if hit_rate_limit(
            scope="password_reset_request",
            identity=f"{ip}:{email}",
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

        request_password_reset_for_email(
            email=serializer.validated_data["email"], request=request
        )
        return Response(
            {
                "detail": (
                    "Si el correo existe en el sistema, se envio un enlace para restablecer la contraseña."
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
