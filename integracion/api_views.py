"""Vistas REST para la integración con la Ticketera.

SISOC actúa como fuente de verdad de credenciales: la Ticketera crea
usuarios y verifica credenciales contra estos endpoints en cada login.
"""

from datetime import timedelta

from auditlog.models import LogEntry
from django.conf import settings
from django.contrib.auth import authenticate, password_validation
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from audittrail.context import audit_context
from core.api_auth import HasAPIKey
from integracion.api_serializers import (
    TicketeraAuthCambiarPasswordResponseSerializer,
    TicketeraAuthCambiarPasswordSerializer,
    TicketeraAuthInvalidSerializer,
    TicketeraAuthVerificarResponseSerializer,
    TicketeraAuthVerificarSerializer,
    TicketeraErrorSerializer,
    TicketeraUsuarioCreateSerializer,
    TicketeraUsuarioResponseSerializer,
)
from users.models import Profile
from users.rate_limits import hit_rate_limit
from users.services_auth import change_password_for_authenticated_user


AUDIT_SOURCE = "integracion:ticketera"


def _integracion_disabled_response() -> Response:
    """Respuesta uniforme cuando la integración está deshabilitada por flag."""
    return Response(
        {
            "error": "integration_disabled",
            "message": "La integración con la Ticketera está deshabilitada.",
        },
        status=status.HTTP_503_SERVICE_UNAVAILABLE,
    )


@extend_schema(tags=["Integración Ticketera"])
class TicketeraUsuarioCreateView(APIView):
    """Crea (o reconcilia) un usuario solicitado por la Ticketera.

    - Idempotente cuando el usuario ya existe con `profile.source == "ticketera"`.
    - 409 cuando el username ya existe con otro source (colisión real).
    """

    permission_classes = [HasAPIKey]

    def _existing_user_response(self, existing):
        """Resuelve idempotencia (200) o conflicto (409) para un usuario ya creado.

        Mismo criterio que el camino normal: si el username pertenece a un alta de
        la Ticketera responde 200 (idempotente); si pertenece a otro origen, 409.
        """
        existing_source = getattr(getattr(existing, "profile", None), "source", "")
        if existing_source == "ticketera":
            return Response(
                {
                    "id": existing.id,
                    "username": existing.username,
                    "email": existing.email,
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "error": "username_taken",
                "message": "El nombre de usuario ya está registrado.",
            },
            status=status.HTTP_409_CONFLICT,
        )

    @extend_schema(
        summary="Alta o reconciliación de usuario desde la Ticketera",
        request=TicketeraUsuarioCreateSerializer,
        responses={
            201: OpenApiResponse(
                response=TicketeraUsuarioResponseSerializer,
                description="Usuario creado.",
            ),
            200: OpenApiResponse(
                response=TicketeraUsuarioResponseSerializer,
                description="Usuario ya existía con source=ticketera (idempotente).",
            ),
            400: OpenApiResponse(
                description=(
                    "Payload inválido: campos faltantes o contraseña que no "
                    "cumple las políticas de seguridad."
                ),
            ),
            409: OpenApiResponse(
                response=TicketeraErrorSerializer,
                description="El username ya existe con otro origen.",
            ),
            503: OpenApiResponse(
                response=TicketeraErrorSerializer,
                description="Integración deshabilitada por configuración.",
            ),
        },
    )
    def post(self, request):
        if not settings.INTEGRACION_TICKETERA_ENABLED:
            return _integracion_disabled_response()

        serializer = TicketeraUsuarioCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        username = data["username"]
        source = data.get("source", "ticketera")

        # Chequeo case-insensitive: "Juan.Perez" y "juan.perez" no deben esquivar
        # la idempotencia ni el 409. El username se guarda tal cual se recibe para
        # no romper authenticate() (backend default, case-sensitive en username).
        existing = User.objects.filter(username__iexact=username).first()
        if existing is not None:
            return self._existing_user_response(existing)

        try:
            password_validation.validate_password(
                data["password"],
                user=User(
                    username=username,
                    email=data["email"],
                    first_name=data.get("first_name", ""),
                    last_name=data.get("last_name", ""),
                ),
            )
        except DjangoValidationError as exc:
            return Response(
                {"password": list(getattr(exc, "messages", [str(exc)]))},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with audit_context(
                source=AUDIT_SOURCE,
                extra={"remote_source": source},
            ):
                with transaction.atomic():
                    user = User.objects.create_user(
                        username=username,
                        email=data["email"],
                        password=data["password"],
                        first_name=data.get("first_name", ""),
                        last_name=data.get("last_name", ""),
                    )
                    profile, _ = Profile.objects.get_or_create(user=user)
                    profile.must_change_password = True
                    profile.source = source
                    # La temporal de Ticketera expira igual que en el flujo
                    # PWA/web (ver generate_temporary_password_for_user).
                    profile.initial_password_expires_at = timezone.now() + timedelta(
                        hours=settings.INITIAL_PASSWORD_MAX_AGE_HOURS
                    )
                    profile.save(
                        update_fields=[
                            "must_change_password",
                            "source",
                            "initial_password_expires_at",
                        ]
                    )
        except IntegrityError:
            # Carrera: otro request creó el mismo username entre el chequeo previo
            # y el create_user. Reconciliamos con la misma lógica idempotente/409.
            existing = User.objects.filter(username__iexact=username).first()
            if existing is not None:
                return self._existing_user_response(existing)
            raise

        return Response(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["Integración Ticketera"])
class TicketeraAuthVerificarView(APIView):
    """Verifica credenciales de un usuario por cuenta de la Ticketera."""

    permission_classes = [HasAPIKey]

    @extend_schema(
        summary="Verificación de credenciales por cuenta de la Ticketera",
        request=TicketeraAuthVerificarSerializer,
        responses={
            200: OpenApiResponse(
                response=TicketeraAuthVerificarResponseSerializer,
                description="Credenciales válidas.",
            ),
            401: OpenApiResponse(
                response=TicketeraAuthInvalidSerializer,
                description="Credenciales inválidas o usuario inactivo.",
            ),
            429: OpenApiResponse(
                response=TicketeraErrorSerializer,
                description="Demasiados intentos (rate limit).",
            ),
            503: OpenApiResponse(
                response=TicketeraErrorSerializer,
                description="Integración deshabilitada por configuración.",
            ),
        },
    )
    def post(self, request):
        if not settings.INTEGRACION_TICKETERA_ENABLED:
            return _integracion_disabled_response()

        serializer = TicketeraAuthVerificarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        username = data["username"]
        password = data["password"]
        source = data.get("source", "ticketera")

        # Identidad ip:username: rotar usernames desde una IP ya no resetea por
        # completo el contador (mismo patrón que PasswordResetRequestViewSet).
        ip = request.META.get("REMOTE_ADDR", "anon")
        if hit_rate_limit(
            scope="ticketera_verificar",
            identity=f"{ip}:{username}",
            limit=10,
            window_seconds=300,
        ):
            return Response(
                {
                    "error": "too_many_attempts",
                    "message": "Demasiados intentos. Esperá unos minutos.",
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        user = authenticate(username=username, password=password)
        if user is None or not user.is_active:
            return Response(
                {"valid": False, "error": "invalid_credentials"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        with audit_context(
            source=AUDIT_SOURCE,
            extra={"remote_source": source},
        ):
            previous_login = user.last_login
            user.last_login = timezone.now()
            user.save(update_fields=["last_login"])
            # last_login está excluido del diff de auditlog: guardar solo ese
            # campo no genera LogEntry, así que registramos el acceso explícito.
            LogEntry.objects.log_create(
                user,
                action=LogEntry.Action.ACCESS,
                changes={
                    "last_login": [
                        previous_login.isoformat() if previous_login else None,
                        user.last_login.isoformat(),
                    ]
                },
                actor=user,
                additional_data={
                    "audittrail_source": AUDIT_SOURCE,
                    "audittrail_context": {"remote_source": source},
                },
            )

        must_change_password = bool(
            getattr(getattr(user, "profile", None), "must_change_password", False)
        )

        return Response(
            {
                "valid": True,
                "must_change_password": must_change_password,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=["Integración Ticketera"])
class TicketeraAuthCambiarPasswordView(APIView):
    """Cierra el ciclo de contraseña temporal por cuenta de la Ticketera.

    Verifica la temporal vigente y fija la contraseña definitiva, bajando
    `must_change_password`. La integración no emite Token DRF (la sesión la
    administra la Ticketera), por eso este canal reemplaza al flujo web
    (`PasswordChangeRequiredViewSet`, que exige TokenAuth) y al middleware de
    primer ingreso (que exige sesión web y exime `/api/`).
    """

    permission_classes = [HasAPIKey]

    @extend_schema(
        summary="Cambio de contraseña temporal por cuenta de la Ticketera",
        request=TicketeraAuthCambiarPasswordSerializer,
        responses={
            200: OpenApiResponse(
                response=TicketeraAuthCambiarPasswordResponseSerializer,
                description=(
                    "Contraseña actualizada; must_change_password queda en false."
                ),
            ),
            400: OpenApiResponse(
                description=(
                    "new_password no cumple las políticas de seguridad o es "
                    "igual a la contraseña actual."
                ),
            ),
            401: OpenApiResponse(
                response=TicketeraErrorSerializer,
                description="Credenciales inválidas o usuario inactivo.",
            ),
            429: OpenApiResponse(
                response=TicketeraErrorSerializer,
                description="Demasiados intentos (rate limit).",
            ),
            503: OpenApiResponse(
                response=TicketeraErrorSerializer,
                description="Integración deshabilitada por configuración.",
            ),
        },
    )
    def post(self, request):
        if not settings.INTEGRACION_TICKETERA_ENABLED:
            return _integracion_disabled_response()

        serializer = TicketeraAuthCambiarPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        username = data["username"]
        current_password = data["current_password"]
        new_password = data["new_password"]
        source = data.get("source", "ticketera")

        # Identidad ip:username, igual que verificar: rotar usernames desde una
        # IP no resetea por completo el contador.
        ip = request.META.get("REMOTE_ADDR", "anon")
        if hit_rate_limit(
            scope="ticketera_cambiar_password",
            identity=f"{ip}:{username}",
            limit=10,
            window_seconds=300,
        ):
            return Response(
                {
                    "error": "too_many_attempts",
                    "message": "Demasiados intentos. Esperá unos minutos.",
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        user = authenticate(username=username, password=current_password)
        if user is None or not user.is_active:
            return Response(
                {"error": "invalid_credentials"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if new_password == current_password:
            return Response(
                {
                    "new_password": [
                        "La nueva contraseña debe ser distinta de la actual."
                    ]
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            password_validation.validate_password(new_password, user=user)
        except DjangoValidationError as exc:
            return Response(
                {"new_password": list(getattr(exc, "messages", [str(exc)]))},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with audit_context(
            source=AUDIT_SOURCE,
            extra={"remote_source": source},
        ):
            with transaction.atomic():
                change_password_for_authenticated_user(
                    user=user,
                    new_password=new_password,
                )
                # `password` está excluido del diff de auditlog y el Profile no
                # es un modelo trackeado: sin un LogEntry explícito el cambio no
                # quedaría en el historial (mismo motivo que el ACCESS de
                # verificar con last_login). Registramos el cambio con el valor
                # redactado.
                LogEntry.objects.log_create(
                    user,
                    action=LogEntry.Action.UPDATE,
                    changes={"password": ["***", "***"]},
                    actor=user,
                    additional_data={
                        "audittrail_source": AUDIT_SOURCE,
                        "audittrail_context": {"remote_source": source},
                    },
                )

        return Response(
            {"changed": True, "must_change_password": False},
            status=status.HTTP_200_OK,
        )
