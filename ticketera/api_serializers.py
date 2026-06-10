"""Serializers para la API server-to-server con la Ticketera."""

# DTOs de request/response: no implementan create()/update() de BaseSerializer
# porque no se usan para .save(). W0223 (abstract-method) es falso positivo de
# DRF para serializers de solo validación/salida.
# pylint: disable=abstract-method

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


class TicketeraUsuarioPatchSerializer(serializers.Serializer):
    """Payload para editar datos básicos de un usuario provisionado por la Ticketera.

    Todos los campos son opcionales. Los campos no incluidos en la lista
    (username, password, is_active, source) no son editables por este canal;
    `source` se acepta solo como hint informativo para auditoría.
    """

    email = serializers.EmailField(max_length=254, required=False)
    first_name = serializers.CharField(max_length=150, allow_blank=True, required=False)
    last_name = serializers.CharField(max_length=150, allow_blank=True, required=False)
    source = serializers.CharField(max_length=50, required=False, default="ticketera")


class TicketeraSolicitarResetSerializer(serializers.Serializer):
    """Payload para iniciar el reset de contraseña desde la Ticketera.

    Mismo XOR que `users.api_serializers.PasswordResetRequestSerializer`: se
    espera exactamente uno de ``username`` o ``email``.
    """

    username = serializers.CharField(max_length=150, required=False)
    email = serializers.EmailField(max_length=254, required=False)
    source = serializers.CharField(max_length=50, required=False, default="ticketera")

    def validate(self, attrs):
        email = (attrs.get("email") or "").strip()
        username = (attrs.get("username") or "").strip()

        if bool(email) == bool(username):
            raise serializers.ValidationError(
                {"detail": ("Debe enviar email o username para solicitar el reseteo.")}
            )

        if username:
            attrs["username"] = username
            attrs.pop("email", None)
        else:
            attrs["email"] = email
            attrs.pop("username", None)
        return attrs


class TicketeraUsuarioResponseSerializer(serializers.Serializer):
    """Datos del usuario devueltos al crear o reconciliar (201/200)."""

    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()


class TicketeraUsuarioDetailSerializer(serializers.Serializer):
    """Snapshot completo devuelto por el PATCH de usuario (200)."""

    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()
    first_name = serializers.CharField(allow_blank=True)
    last_name = serializers.CharField(allow_blank=True)


class TicketeraSolicitarResetResponseSerializer(serializers.Serializer):
    """Respuesta genérica del solicitar-reset (200 anti-enumeration)."""

    detail = serializers.CharField()


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
