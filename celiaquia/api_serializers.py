"""Serializers de la API REST de Celiaquia.

Se arman desde los modelos con `ModelSerializer`, pero **nunca** con
`fields = "__all__"`: varios modelos guardan FileFields con rutas internas y FKs
a `User` que no deben salir de la aplicacion. Los campos se listan a mano.

Los serializers son de lectura: las escrituras pasan por
`celiaquia/services/`, donde vive la maquina de estados.
"""

from rest_framework import serializers

from celiaquia.models import (
    AsignacionTecnico,
    CupoMovimiento,
    DocumentoLegajo,
    EstadoExpediente,
    EstadoLegajo,
    Expediente,
    ExpedienteCiudadano,
    ExpedienteEstadoHistorial,
    Organismo,
    PagoExpediente,
    PagoNomina,
    ProvinciaCupo,
    Subsanacion,
    TipoCruce,
    TipoDocumento,
)


class UsuarioResumenSerializer(serializers.Serializer):
    """Identidad minima de un usuario: nunca mail, permisos ni credenciales."""

    id = serializers.IntegerField(read_only=True)
    nombre = serializers.SerializerMethodField()

    def get_nombre(self, obj) -> str:
        return obj.get_full_name() or obj.username

    def create(self, validated_data):
        raise serializers.ValidationError("Serializer de solo lectura.")

    def update(self, instance, validated_data):
        raise serializers.ValidationError("Serializer de solo lectura.")


# --- Catalogos -------------------------------------------------------------


class _CatalogoNombreSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ["id", "nombre"]


class EstadoExpedienteSerializer(_CatalogoNombreSerializer):
    class Meta(_CatalogoNombreSerializer.Meta):
        model = EstadoExpediente


class EstadoLegajoSerializer(_CatalogoNombreSerializer):
    class Meta(_CatalogoNombreSerializer.Meta):
        model = EstadoLegajo


class OrganismoSerializer(_CatalogoNombreSerializer):
    class Meta(_CatalogoNombreSerializer.Meta):
        model = Organismo


class TipoCruceSerializer(_CatalogoNombreSerializer):
    class Meta(_CatalogoNombreSerializer.Meta):
        model = TipoCruce


class TipoDocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoDocumento
        fields = ["id", "nombre", "descripcion", "requerido", "orden", "activo"]


# --- Expediente ------------------------------------------------------------


class ExpedienteSerializer(serializers.ModelSerializer):
    estado = serializers.CharField(source="estado.nombre", read_only=True)
    provincia = serializers.SerializerMethodField()
    usuario_provincia = UsuarioResumenSerializer(read_only=True)
    legajos_total = serializers.SerializerMethodField()

    class Meta:
        model = Expediente
        fields = [
            "id",
            "numero_expediente",
            "estado",
            "provincia",
            "usuario_provincia",
            "observaciones",
            "legajos_total",
            "fecha_creacion",
            "fecha_modificacion",
            "fecha_cierre",
        ]

    def get_provincia(self, obj) -> str:
        """Provincia derivada del perfil de quien creo el expediente.

        El listado web la deriva de los ciudadanos con un Subquery; aca se usa
        el valor anotado cuando el ViewSet lo provee y se cae al perfil.
        """

        derivada = getattr(obj, "provincia_derivada", None)
        if derivada:
            return derivada
        perfil = getattr(obj.usuario_provincia, "profile", None)
        provincia = getattr(perfil, "provincia", None)
        return getattr(provincia, "nombre", "") or ""

    def get_legajos_total(self, obj) -> int:
        anotado = getattr(obj, "legajos_total_count", None)
        if anotado is not None:
            return anotado
        return obj.expediente_ciudadanos.count()


class ExpedienteEstadoHistorialSerializer(serializers.ModelSerializer):
    estado = serializers.CharField(source="estado.nombre", read_only=True)
    usuario = UsuarioResumenSerializer(read_only=True)

    class Meta:
        model = ExpedienteEstadoHistorial
        fields = ["id", "estado", "usuario", "fecha"]


class AsignacionTecnicoSerializer(serializers.ModelSerializer):
    tecnico = UsuarioResumenSerializer(read_only=True)

    class Meta:
        model = AsignacionTecnico
        fields = ["id", "tecnico", "fecha_asignacion", "activa"]


# --- Legajos ---------------------------------------------------------------


class LegajoSerializer(serializers.ModelSerializer):
    """`ExpedienteCiudadano` es el legajo de una persona dentro del expediente."""

    estado = serializers.CharField(source="estado.nombre", read_only=True)
    ciudadano_id = serializers.IntegerField(read_only=True)
    ciudadano = serializers.SerializerMethodField()
    documento = serializers.SerializerMethodField()

    class Meta:
        model = ExpedienteCiudadano
        fields = [
            "id",
            "expediente_id",
            "ciudadano_id",
            "ciudadano",
            "documento",
            "estado",
            "rol",
            "archivos_ok",
            "cruce_ok",
            "observacion_cruce",
            "revision_tecnico",
            "resultado_sintys",
            "estado_cupo",
            "es_titular_activo",
            "estado_validacion_renaper",
            "subsanacion_tipo",
            "subsanacion_motivo",
            "subsanacion_solicitada_en",
            "subsanacion_enviada_en",
            "creado_en",
            "modificado_en",
        ]

    def get_ciudadano(self, obj) -> str:
        ciudadano = obj.ciudadano
        nombre = f"{ciudadano.apellido or ''} {ciudadano.nombre or ''}".strip()
        return nombre or f"#{ciudadano.pk}"

    def get_documento(self, obj) -> str:
        return str(getattr(obj.ciudadano, "documento", "") or "")


class DocumentoLegajoSerializer(serializers.ModelSerializer):
    tipo_documento = serializers.CharField(
        source="tipo_documento.nombre", read_only=True
    )
    usuario_carga = UsuarioResumenSerializer(read_only=True)
    archivo_url = serializers.SerializerMethodField()

    class Meta:
        model = DocumentoLegajo
        fields = [
            "id",
            "legajo_id",
            "tipo_documento",
            "archivo_url",
            "observaciones",
            "usuario_carga",
            "fecha_carga",
        ]

    def get_archivo_url(self, obj) -> str:
        """URL absoluta del archivo; nunca la ruta de almacenamiento."""

        archivo = getattr(obj, "archivo", None)
        if not archivo:
            return ""
        request = self.context.get("request")
        url = archivo.url
        return request.build_absolute_uri(url) if request else url


class SubsanacionSerializer(serializers.ModelSerializer):
    solicitada_por = UsuarioResumenSerializer(read_only=True)
    respondida_por = UsuarioResumenSerializer(read_only=True)

    class Meta:
        model = Subsanacion
        fields = [
            "id",
            "legajo_id",
            "estado",
            "motivo_general",
            "solicitada_por",
            "solicitada_en",
            "respondida_por",
            "respondida_en",
        ]


# --- Cupos -----------------------------------------------------------------


class ProvinciaCupoSerializer(serializers.ModelSerializer):
    provincia = serializers.CharField(source="provincia.nombre", read_only=True)
    disponibles = serializers.SerializerMethodField()

    class Meta:
        model = ProvinciaCupo
        fields = ["id", "provincia", "total_asignado", "usados", "disponibles"]

    def get_disponibles(self, obj) -> int:
        return max((obj.total_asignado or 0) - (obj.usados or 0), 0)


class CupoMovimientoSerializer(serializers.ModelSerializer):
    provincia = serializers.CharField(source="provincia.nombre", read_only=True)
    usuario = UsuarioResumenSerializer(read_only=True)

    class Meta:
        model = CupoMovimiento
        fields = [
            "id",
            "provincia",
            "expediente_id",
            "legajo_id",
            "tipo",
            "delta",
            "motivo",
            "usuario",
            "creado_en",
        ]


# --- Pagos -----------------------------------------------------------------


class PagoExpedienteSerializer(serializers.ModelSerializer):
    provincia = serializers.CharField(source="provincia.nombre", read_only=True)

    class Meta:
        model = PagoExpediente
        fields = [
            "id",
            "provincia",
            "periodo",
            "estado",
            "total_candidatos",
            "total_validados",
            "total_excluidos",
            "creado_en",
            "modificado_en",
        ]


class PagoNominaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PagoNomina
        fields = [
            "id",
            "pago_id",
            "legajo_id",
            "documento",
            "nombre",
            "apellido",
            "estado",
            "observacion",
            "creado_en",
        ]


# --- Entradas de las acciones ---------------------------------------------


class AsignarTecnicoSerializer(serializers.Serializer):
    tecnico_id = serializers.IntegerField()

    def create(self, validated_data):
        raise serializers.ValidationError("Serializer de solo entrada.")

    def update(self, instance, validated_data):
        raise serializers.ValidationError("Serializer de solo entrada.")


class SolicitarSubsanacionSerializer(serializers.Serializer):
    motivo = serializers.CharField(max_length=2000)

    def create(self, validated_data):
        raise serializers.ValidationError("Serializer de solo entrada.")

    def update(self, instance, validated_data):
        raise serializers.ValidationError("Serializer de solo entrada.")


class AccionResultadoSerializer(serializers.Serializer):
    """Respuesta uniforme de las acciones que delegan en un service."""

    detail = serializers.CharField()
    expediente = ExpedienteSerializer(required=False)

    def create(self, validated_data):
        raise serializers.ValidationError("Serializer de solo lectura.")

    def update(self, instance, validated_data):
        raise serializers.ValidationError("Serializer de solo lectura.")
