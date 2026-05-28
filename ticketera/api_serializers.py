"""Serializers para la API server-to-server con la Ticketera."""

from rest_framework import serializers


class TicketeraUsuarioCreateSerializer(serializers.Serializer):
    """Payload para crear o reconciliar usuarios desde la Ticketera."""

    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(max_length=254)
    first_name = serializers.CharField(max_length=150, allow_blank=True, required=False)
    last_name = serializers.CharField(max_length=150, allow_blank=True, required=False)
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    source = serializers.CharField(max_length=50, required=False, default="ticketera")


class TicketeraAuthVerificarSerializer(serializers.Serializer):
    """Payload para verificar credenciales desde la Ticketera."""

    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    source = serializers.CharField(max_length=50, required=False, default="ticketera")


class TicketeraAuthCambiarPasswordSerializer(serializers.Serializer):
    """Payload para fijar la contraseña definitiva y cerrar el ciclo temporal."""

    username = serializers.CharField(max_length=150)
    current_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)
    source = serializers.CharField(max_length=50, required=False, default="ticketera")


class TicketeraUsuarioResponseSerializer(serializers.Serializer):
    """Datos del usuario devueltos al crear o reconciliar (201/200)."""

    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()


class TicketeraAuthVerificarUserSerializer(serializers.Serializer):
    """Usuario embebido en una verificación de credenciales válida."""

    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()


class TicketeraAuthVerificarResponseSerializer(serializers.Serializer):
    """Respuesta de una verificación de credenciales válida (200)."""

    valid = serializers.BooleanField()
    must_change_password = serializers.BooleanField()
    user = TicketeraAuthVerificarUserSerializer()


class TicketeraAuthCambiarPasswordResponseSerializer(serializers.Serializer):
    """Respuesta de un cambio de contraseña exitoso (200)."""

    changed = serializers.BooleanField()
    must_change_password = serializers.BooleanField()


class TicketeraAuthInvalidSerializer(serializers.Serializer):
    """Respuesta de credenciales inválidas o usuario inactivo (401)."""

    valid = serializers.BooleanField()
    error = serializers.CharField()


class TicketeraErrorSerializer(serializers.Serializer):
    """Cuerpo de error genérico de la integración (409/429/503)."""

    error = serializers.CharField()
    message = serializers.CharField(required=False)
