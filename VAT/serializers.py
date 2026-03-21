from rest_framework import serializers
from VAT.models import (
    Centro,
    Categoria,
    Actividad,
    ActividadCentro,
    ParticipanteActividad,
    ParticipanteActividadHistorial,
    ModalidadInstitucional,
    Sector,
    Subsector,
    TituloReferencia,
    ModalidadCursada,
    PlanVersionCurricular,
)
from core.models import Provincia, Municipio, Localidad


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ["id", "nombre"]


class ActividadSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source="categoria.nombre", read_only=True)

    class Meta:
        model = Actividad
        fields = ["id", "nombre", "categoria", "categoria_nombre"]


class ActividadCentroSerializer(serializers.ModelSerializer):
    actividad_nombre = serializers.CharField(source="actividad.nombre", read_only=True)
    centro_nombre = serializers.CharField(source="centro.nombre", read_only=True)
    dias_nombres = serializers.SerializerMethodField()

    def get_dias_nombres(self, obj: ActividadCentro) -> list[str]:
        return [dia.nombre for dia in obj.dias.all()]

    class Meta:
        model = ActividadCentro
        fields = [
            "id",
            "centro",
            "centro_nombre",
            "actividad",
            "actividad_nombre",
            "cantidad_personas",
            "dias",
            "dias_nombres",
            "horariosdesde",
            "horarioshasta",
            "precio",
            "estado",
        ]


class CentroSerializer(serializers.ModelSerializer):
    referente_nombre = serializers.CharField(
        source="referente.get_full_name", read_only=True
    )
    provincia_nombre = serializers.CharField(source="provincia.nombre", read_only=True)
    municipio_nombre = serializers.CharField(source="municipio.nombre", read_only=True)
    localidad_nombre = serializers.CharField(source="localidad.nombre", read_only=True)
    modalidad_institucional_nombre = serializers.CharField(
        source="modalidad_institucional.nombre", read_only=True
    )
    categorias_actividades = serializers.SerializerMethodField()

    def get_categorias_actividades(self, obj):
        categorias = Categoria.objects.filter(
            actividad__actividadcentro__centro=obj
        ).distinct()
        return CategoriaSerializer(categorias, many=True).data

    class Meta:
        model = Centro
        fields = [
            "id",
            "nombre",
            "referente",
            "referente_nombre",
            "codigo",
            "activo",
            "provincia",
            "provincia_nombre",
            "municipio",
            "municipio_nombre",
            "localidad",
            "localidad_nombre",
            "domicilio_actividad",
            "telefono",
            "celular",
            "correo",
            "nombre_referente",
            "apellido_referente",
            "modalidad_institucional",
            "modalidad_institucional_nombre",
            "tipo_gestion",
            "clase_institucion",
            "situacion",
            "fecha_alta",
            "categorias_actividades",
        ]


class ParticipanteActividadHistorialSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(
        source="usuario.get_full_name", read_only=True
    )

    class Meta:
        model = ParticipanteActividadHistorial
        fields = [
            "id",
            "estado_anterior",
            "estado_nuevo",
            "fecha_cambio",
            "usuario",
            "usuario_nombre",
        ]


class ParticipanteActividadSerializer(serializers.ModelSerializer):
    ciudadano_nombre = serializers.CharField(
        source="ciudadano.get_full_name", read_only=True
    )
    actividad_nombre = serializers.CharField(
        source="actividad_centro.actividad.nombre", read_only=True
    )
    historial = ParticipanteActividadHistorialSerializer(many=True, read_only=True)

    class Meta:
        model = ParticipanteActividad
        fields = [
            "id",
            "actividad_centro",
            "actividad_nombre",
            "ciudadano",
            "ciudadano_nombre",
            "estado",
            "fecha_registro",
            "fecha_modificacion",
            "historial",
        ]


class ProvinciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Provincia
        fields = ["id", "nombre"]


class MunicipioSerializer(serializers.ModelSerializer):
    provincia_nombre = serializers.CharField(source="provincia.nombre", read_only=True)

    class Meta:
        model = Municipio
        fields = ["id", "nombre", "provincia", "provincia_nombre"]


class LocalidadSerializer(serializers.ModelSerializer):
    municipio_nombre = serializers.CharField(source="municipio.nombre", read_only=True)
    provincia_nombre = serializers.CharField(
        source="municipio.provincia.nombre", read_only=True
    )

    class Meta:
        model = Localidad
        fields = ["id", "nombre", "municipio", "municipio_nombre", "provincia_nombre"]


class ModalidadInstitucionalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModalidadInstitucional
        fields = ["id", "nombre", "descripcion", "activo", "fecha_creacion", "fecha_modificacion"]
        read_only_fields = ["fecha_creacion", "fecha_modificacion"]


class SectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sector
        fields = ["id", "nombre", "descripcion"]


class SubsectorSerializer(serializers.ModelSerializer):
    sector_nombre = serializers.CharField(source="sector.nombre", read_only=True)

    class Meta:
        model = Subsector
        fields = ["id", "sector", "sector_nombre", "nombre", "descripcion"]


class TituloReferenciaSerializer(serializers.ModelSerializer):
    sector_nombre = serializers.CharField(source="sector.nombre", read_only=True)
    subsector_nombre = serializers.CharField(source="subsector.nombre", read_only=True)

    class Meta:
        model = TituloReferencia
        fields = [
            "id",
            "sector",
            "sector_nombre",
            "subsector",
            "subsector_nombre",
            "codigo_referencia",
            "nombre",
            "descripcion",
            "activo",
        ]


class ModalidadCursadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModalidadCursada
        fields = ["id", "nombre", "descripcion", "activo"]


class PlanVersionCurricularSerializer(serializers.ModelSerializer):
    titulo_referencia_nombre = serializers.CharField(
        source="titulo_referencia.nombre", read_only=True
    )
    modalidad_cursada_nombre = serializers.CharField(
        source="modalidad_cursada.nombre", read_only=True
    )

    class Meta:
        model = PlanVersionCurricular
        fields = [
            "id",
            "titulo_referencia",
            "titulo_referencia_nombre",
            "modalidad_cursada",
            "modalidad_cursada_nombre",
            "normativa",
            "version",
            "horas_reloj",
            "nivel_requerido",
            "nivel_certifica",
            "frecuencia",
            "activo",
        ]
