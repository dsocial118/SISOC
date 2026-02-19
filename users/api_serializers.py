from rest_framework import serializers

from users.models import AccesoComedorPWA
from users.services import UserPermissionService
from users.services_pwa import get_pwa_context


class UserContextSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    is_superuser = serializers.BooleanField(read_only=True)
    is_staff = serializers.BooleanField(read_only=True)
    groups = serializers.SerializerMethodField()
    profile = serializers.SerializerMethodField()
    scope = serializers.SerializerMethodField()
    pwa = serializers.SerializerMethodField()

    def _raise_read_only(self):
        raise NotImplementedError("Serializer de solo lectura.")

    def create(self, validated_data):
        return self._raise_read_only()

    def update(self, instance, validated_data):
        return self._raise_read_only()

    def get_groups(self, obj):
        if not getattr(obj, "is_authenticated", False):
            return []
        return list(obj.groups.values_list("name", flat=True))

    def get_profile(self, obj):
        profile = getattr(obj, "profile", None)
        if not profile:
            return None
        return {
            "rol": profile.rol,
            "provincia_id": profile.provincia_id,
            "es_usuario_provincial": profile.es_usuario_provincial,
            "es_coordinador": profile.es_coordinador,
            "duplas_asignadas": list(
                profile.duplas_asignadas.values_list("id", flat=True)
            ),
        }

    def get_scope(self, obj):
        if not getattr(obj, "is_authenticated", False):
            return {}
        is_coordinador, duplas_ids = UserPermissionService.get_coordinador_duplas(obj)
        profile = getattr(obj, "profile", None)
        return {
            "is_coordinador": is_coordinador,
            "duplas_ids": duplas_ids,
            "es_usuario_provincial": getattr(profile, "es_usuario_provincial", False),
            "provincia_id": getattr(profile, "provincia_id", None),
        }

    def get_pwa(self, obj):
        return get_pwa_context(obj)


class OperadorCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def _raise_read_only(self):
        raise NotImplementedError("Serializer de solo lectura.")

    def create(self, validated_data):
        return self._raise_read_only()

    def update(self, instance, validated_data):
        return self._raise_read_only()


class OperadorListSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="user_id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = AccesoComedorPWA
        fields = (
            "id",
            "username",
            "email",
            "activo",
            "fecha_creacion",
        )


class OperadorCreateResponseSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="user_id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    comedor_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = AccesoComedorPWA
        fields = (
            "id",
            "username",
            "email",
            "comedor_id",
            "rol",
            "activo",
        )
