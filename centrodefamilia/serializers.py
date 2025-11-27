from rest_framework import serializers
from centrodefamilia.models import (
    Centro,
    Categoria,
    Actividad,
    ActividadCentro,
    ParticipanteActividad,
    ParticipanteActividadHistorial,
    Beneficiario,
    Responsable,
    BeneficiarioResponsable,
    CabalArchivo,
    InformeCabalRegistro,
)


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

    def get_dias_nombres(self, obj):
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

    class Meta:
        model = Centro
        fields = [
            "id",
            "nombre",
            "referente",
            "referente_nombre",
            "tipo",
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
        ]


class ResponsableSerializer(serializers.ModelSerializer):
    provincia_nombre = serializers.CharField(source="provincia.nombre", read_only=True)
    municipio_nombre = serializers.CharField(source="municipio.nombre", read_only=True)
    localidad_nombre = serializers.CharField(source="localidad.nombre", read_only=True)

    class Meta:
        model = Responsable
        fields = [
            "id",
            "vinculo_parental",
            "cuil",
            "dni",
            "apellido",
            "nombre",
            "genero",
            "fecha_nacimiento",
            "provincia",
            "provincia_nombre",
            "municipio",
            "municipio_nombre",
            "localidad",
            "localidad_nombre",
            "calle",
            "altura",
            "correo_electronico",
            "numero_celular",
        ]


class BeneficiarioSerializer(serializers.ModelSerializer):
    responsable_nombre = serializers.CharField(
        source="responsable.get_full_name", read_only=True
    )
    provincia_nombre = serializers.CharField(source="provincia.nombre", read_only=True)
    municipio_nombre = serializers.CharField(source="municipio.nombre", read_only=True)
    localidad_nombre = serializers.CharField(source="localidad.nombre", read_only=True)

    class Meta:
        model = Beneficiario
        fields = [
            "id",
            "cuil",
            "dni",
            "apellido",
            "nombre",
            "genero",
            "fecha_nacimiento",
            "domicilio",
            "provincia",
            "provincia_nombre",
            "municipio",
            "municipio_nombre",
            "localidad",
            "localidad_nombre",
            "nivel_educativo_actual",
            "maximo_nivel_educativo",
            "responsable",
            "responsable_nombre",
            "actividad_preferida",
            "actividades_extracurriculares",
        ]


class BeneficiarioResponsableSerializer(serializers.ModelSerializer):
    beneficiario_nombre = serializers.CharField(
        source="beneficiario.get_full_name", read_only=True
    )
    responsable_nombre = serializers.CharField(
        source="responsable.get_full_name", read_only=True
    )

    class Meta:
        model = BeneficiarioResponsable
        fields = [
            "id",
            "beneficiario",
            "beneficiario_nombre",
            "responsable",
            "responsable_nombre",
            "vinculo_parental",
        ]


class ParticipanteActividadHistorialSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source="usuario.get_full_name", read_only=True)

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


class InformeCabalRegistroSerializer(serializers.ModelSerializer):
    centro_nombre = serializers.CharField(source="centro.nombre", read_only=True)

    class Meta:
        model = InformeCabalRegistro
        fields = [
            "id",
            "centro",
            "centro_nombre",
            "nro_tarjeta",
            "nro_auto",
            "nro_comercio",
            "razon_social",
            "importe",
            "fecha_trx",
            "no_coincidente",
            "fila_numero",
        ]


class CabalArchivoSerializer(serializers.ModelSerializer):
    registros = InformeCabalRegistroSerializer(many=True, read_only=True)
    usuario_nombre = serializers.CharField(source="usuario.get_full_name", read_only=True)

    class Meta:
        model = CabalArchivo
        fields = [
            "id",
            "nombre_original",
            "usuario",
            "usuario_nombre",
            "fecha_subida",
            "total_filas",
            "total_validas",
            "total_invalidas",
            "registros",
        ]
