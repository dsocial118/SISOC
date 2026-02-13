from drf_spectacular.utils import extend_schema
from django.contrib.auth import authenticate
from django.core.exceptions import PermissionDenied
from rest_framework import serializers, status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from core.api_auth import HasAPIKeyOrToken
from users.api_serializers import UserContextSerializer


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
    permission_classes = [HasAPIKeyOrToken]

    @extend_schema(responses=UserContextSerializer)
    def list(self, request):
        serializer = UserContextSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
