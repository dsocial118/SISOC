"""Serializers de la API que consume la app DataCalle (contrato D2.5).

Convención: snake_case en el envoltorio; las claves dentro de ``respuestas``
son los ids del cuestionario y no se renombran.
"""

from rest_framework import serializers

from datacalle.models import Encuesta, Relevamiento


class NoSaveSerializer(serializers.Serializer):
    """Serializer de sólo lectura/validación: no persiste por sí mismo."""

    def _raise_read_only(self):
        raise serializers.ValidationError("Serializer de solo lectura.")

    def create(self, validated_data):
        return self._raise_read_only()

    def update(self, instance, validated_data):
        return self._raise_read_only()


class ReferenciaSerializer(NoSaveSerializer):
    id = serializers.IntegerField()
    nombre = serializers.CharField()


class IntegranteEquipoSerializer(NoSaveSerializer):
    id = serializers.IntegerField()
    nombre = serializers.SerializerMethodField()
    dni = serializers.SerializerMethodField()

    def get_nombre(self, obj):
        return obj.get_full_name() or obj.username

    def get_dni(self, obj):
        return getattr(getattr(obj, "profile", None), "dni", "") or ""


class RelevamientoTareaSerializer(serializers.ModelSerializer):
    """La tarea tal como la lee la app (ejemplo en `contrato/ejemplos/`)."""

    provincia = serializers.SerializerMethodField()
    municipio = serializers.SerializerMethodField()
    localidades = serializers.SerializerMethodField()
    dispositivo = serializers.SerializerMethodField()
    equipo = IntegranteEquipoSerializer(many=True, read_only=True)
    cantidad_encuestas = serializers.SerializerMethodField()
    actualizado_en = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = Relevamiento
        fields = (
            "id",
            "denominacion",
            "provincia",
            "municipio",
            "localidades",
            "fase",
            "area_operativa",
            "dispositivo",
            "fecha_inicio",
            "fecha_fin",
            "modalidad_papel",
            "estado",
            "equipo",
            "cantidad_encuestas",
            "observaciones",
            "fecha_cierre",
            "actualizado_en",
        )

    @staticmethod
    def _referencia(obj):
        if obj is None:
            return None
        return {"id": obj.id, "nombre": obj.nombre}

    def get_provincia(self, obj):
        return self._referencia(obj.provincia)

    def get_municipio(self, obj):
        return self._referencia(obj.municipio)

    def get_localidades(self, obj):
        return [self._referencia(loc) for loc in obj.localidades.all()]

    def get_dispositivo(self, obj):
        if obj.dispositivo_id is None:
            return None
        return {"id": obj.dispositivo_id, "nombre": obj.dispositivo.nombre_institucion}

    def get_cantidad_encuestas(self, obj):
        cantidad = getattr(obj, "cantidad_encuestas", None)
        if cantidad is None:
            return obj.encuestas.count()
        return cantidad


class EncuestaSerializer(serializers.ModelSerializer):
    """Caso ya sincronizado, para la lectura descendente."""

    relevamiento_id = serializers.UUIDField(read_only=True)
    relevador_id = serializers.IntegerField(read_only=True)
    actualizado_en = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = Encuesta
        fields = (
            "id",
            "relevamiento_id",
            "relevador_id",
            "origen",
            "variante",
            "estado",
            "fecha_inicio",
            "fecha_hora_fin",
            "respuestas",
            "actualizado_en",
        )


class EncuestaUpsertSerializer(NoSaveSerializer):
    """Cuerpo del ``PUT /encuestas/{uuid}/``."""

    relevamiento_id = serializers.UUIDField()
    variante = serializers.CharField(required=False, allow_blank=True, max_length=32)
    estado = serializers.ChoiceField(choices=Encuesta.Estado.choices)
    fecha_inicio = serializers.DateTimeField(required=False, allow_null=True)
    fecha_hora_fin = serializers.DateTimeField(required=False, allow_null=True)
    respuestas = serializers.JSONField(required=False)

    def validate_respuestas(self, value):
        if value in (None, ""):
            return {}
        if not isinstance(value, dict):
            raise serializers.ValidationError(
                "Debe ser un objeto con las claves del cuestionario."
            )
        return value


class CierreRelevamientoSerializer(NoSaveSerializer):
    """Cuerpo del ``POST /relevamientos/{id}/cerrar/`` (D2.5)."""

    fecha_cierre = serializers.DateTimeField(required=False, allow_null=True)
    lat = serializers.FloatField(
        required=False, allow_null=True, min_value=-90, max_value=90
    )
    lon = serializers.FloatField(
        required=False, allow_null=True, min_value=-180, max_value=180
    )
    observacion_asentamiento = serializers.ListField(
        child=serializers.CharField(max_length=64), required=False
    )
    otra_observacion = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
