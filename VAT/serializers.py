from rest_framework import serializers
from VAT.models import (
    Centro,
    ModalidadInstitucional,
    Sector,
    Subsector,
    TituloReferencia,
    ModalidadCursada,
    PlanVersionCurricular,
    InscripcionOferta,
    Voucher,
    VoucherRecarga,
    VoucherUso,
    # Fase 2
    InstitucionContacto,
    AutoridadInstitucional,
    InstitucionIdentificadorHist,
    InstitucionUbicacion,
    Curso,
    ComisionCurso,
    # Fase 4
    OfertaInstitucional,
    Comision,
    ComisionHorario,
    # Fase 5
    Inscripcion,
    # Fase 7
    Evaluacion,
    ResultadoEvaluacion,
)
from ciudadanos.models import Ciudadano
from core.models import Provincia, Municipio, Localidad


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
        fields = [
            "id",
            "nombre",
            "descripcion",
            "activo",
            "fecha_creacion",
            "fecha_modificacion",
        ]
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
    plan_estudio = serializers.PrimaryKeyRelatedField(
        queryset=PlanVersionCurricular.objects.all(),
        allow_null=True,
        required=False,
    )
    sector = serializers.IntegerField(source="plan_estudio.sector_id", read_only=True)
    sector_nombre = serializers.CharField(
        source="plan_estudio.sector.nombre", read_only=True
    )
    subsector = serializers.IntegerField(
        source="plan_estudio.subsector_id", read_only=True
    )
    subsector_nombre = serializers.CharField(
        source="plan_estudio.subsector.nombre", read_only=True
    )

    class Meta:
        model = TituloReferencia
        fields = [
            "id",
            "plan_estudio",
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
    titulo_referencia = serializers.IntegerField(
        source="titulo_referencia_id", read_only=True
    )
    titulo_referencia_nombre = serializers.CharField(
        source="titulo_referencia.nombre", read_only=True
    )
    sector_nombre = serializers.CharField(source="sector.nombre", read_only=True)
    subsector_nombre = serializers.CharField(source="subsector.nombre", read_only=True)
    modalidad_cursada_nombre = serializers.CharField(
        source="modalidad_cursada.nombre", read_only=True
    )

    class Meta:
        model = PlanVersionCurricular
        fields = [
            "id",
            "titulo_referencia",
            "titulo_referencia_nombre",
            "sector",
            "sector_nombre",
            "subsector",
            "subsector_nombre",
            "modalidad_cursada",
            "modalidad_cursada_nombre",
            "normativa",
            "horas_reloj",
            "nivel_requerido",
            "nivel_certifica",
            "activo",
        ]


class InscripcionOfertaSerializer(serializers.ModelSerializer):
    ciudadano_nombre = serializers.CharField(
        source="ciudadano.nombre_completo", read_only=True
    )
    oferta_nombre = serializers.CharField(source="oferta.nombre", read_only=True)

    class Meta:
        model = InscripcionOferta
        fields = [
            "id",
            "oferta",
            "oferta_nombre",
            "ciudadano",
            "ciudadano_nombre",
            "estado",
            "fecha_inscripcion",
            "fecha_modificacion",
        ]


class VoucherRecargaSerializer(serializers.ModelSerializer):
    autorizado_por_nombre = serializers.CharField(
        source="autorizado_por.get_full_name", read_only=True
    )

    class Meta:
        model = VoucherRecarga
        fields = [
            "id",
            "voucher",
            "cantidad",
            "motivo",
            "fecha_recarga",
            "autorizado_por",
            "autorizado_por_nombre",
        ]
        read_only_fields = ["fecha_recarga", "autorizado_por"]


class VoucherUsoSerializer(serializers.ModelSerializer):
    oferta_nombre = serializers.CharField(
        source="inscripcion_oferta.oferta.plan_curricular.titulo_referencia.nombre",
        read_only=True,
    )

    class Meta:
        model = VoucherUso
        fields = [
            "id",
            "voucher",
            "inscripcion_oferta",
            "oferta_nombre",
            "cantidad_usada",
            "fecha_uso",
        ]
        read_only_fields = ["fecha_uso"]


class VoucherSerializer(serializers.ModelSerializer):
    ciudadano_nombre = serializers.CharField(
        source="ciudadano.nombre_completo", read_only=True
    )
    programa_nombre = serializers.CharField(source="programa.nombre", read_only=True)
    recargas = VoucherRecargaSerializer(many=True, read_only=True)
    usos = VoucherUsoSerializer(many=True, read_only=True)
    dias_para_vencimiento = serializers.SerializerMethodField()

    def get_dias_para_vencimiento(self, obj):
        from datetime import date

        delta = obj.fecha_vencimiento - date.today()
        return delta.days

    class Meta:
        model = Voucher
        fields = [
            "id",
            "ciudadano",
            "ciudadano_nombre",
            "programa",
            "programa_nombre",
            "cantidad_inicial",
            "cantidad_usada",
            "cantidad_disponible",
            "estado",
            "fecha_asignacion",
            "fecha_vencimiento",
            "dias_para_vencimiento",
            "recargas",
            "usos",
            "fecha_creacion",
            "fecha_modificacion",
        ]
        read_only_fields = [
            "cantidad_usada",
            "cantidad_disponible",
            "fecha_creacion",
            "fecha_modificacion",
        ]


# ============================================================================
# FASE 2: INSTITUCIÓN - CONTACTOS E IDENTIFICADORES
# ============================================================================


class InstitucionContactoSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstitucionContacto
        fields = [
            "id",
            "centro",
            "tipo",
            "valor",
            "es_principal",
            "observaciones",
            "vigencia_desde",
            "vigencia_hasta",
            "fecha_creacion",
            "fecha_modificacion",
        ]


class AutoridadInstitucionalSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutoridadInstitucional
        fields = [
            "id",
            "centro",
            "nombre_completo",
            "dni",
            "cargo",
            "email",
            "telefono",
            "es_actual",
            "vigencia_desde",
            "vigencia_hasta",
            "fecha_creacion",
            "fecha_modificacion",
        ]


class InstitucionIdentificadorHistSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstitucionIdentificadorHist
        fields = [
            "id",
            "centro",
            "tipo_identificador",
            "valor_identificador",
            "rol_institucional",
            "es_actual",
            "vigencia_desde",
            "vigencia_hasta",
            "motivo",
            "fecha_creacion",
            "fecha_modificacion",
        ]


class InstitucionUbicacionSerializer(serializers.ModelSerializer):
    localidad_nombre = serializers.CharField(source="localidad.nombre", read_only=True)

    class Meta:
        model = InstitucionUbicacion
        fields = [
            "id",
            "centro",
            "localidad",
            "localidad_nombre",
            "rol_ubicacion",
            "domicilio",
            "es_principal",
            "latitud",
            "longitud",
            "observaciones",
            "vigencia_desde",
            "vigencia_hasta",
            "fecha_creacion",
            "fecha_modificacion",
        ]


# ============================================================================
# CURSOS (CAPA OPERATIVA)
# ============================================================================


class CursoSerializer(serializers.ModelSerializer):
    centro_nombre = serializers.CharField(source="centro.nombre", read_only=True)
    plan_estudio_nombre = serializers.CharField(source="plan_estudio", read_only=True)
    ubicacion_nombre = serializers.CharField(
        source="ubicacion.nombre_ubicacion", read_only=True
    )
    modalidad_nombre = serializers.CharField(source="modalidad.nombre", read_only=True)
    programa = serializers.IntegerField(source="programa_id", read_only=True)
    programa_nombre = serializers.CharField(source="programa.nombre", read_only=True)
    voucher_parametrias = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Curso
        fields = [
            "id",
            "centro",
            "centro_nombre",
            "plan_estudio",
            "plan_estudio_nombre",
            "ubicacion",
            "ubicacion_nombre",
            "nombre",
            "modalidad",
            "modalidad_nombre",
            "programa",
            "programa_nombre",
            "estado",
            "usa_voucher",
            "voucher_parametrias",
            "costo_creditos",
            "observaciones",
            "fecha_creacion",
            "fecha_modificacion",
        ]


class ComisionCursoSerializer(serializers.ModelSerializer):
    curso_nombre = serializers.CharField(source="curso.nombre", read_only=True)
    curso_centro_id = serializers.IntegerField(source="curso.centro_id", read_only=True)

    class Meta:
        model = ComisionCurso
        fields = [
            "id",
            "curso",
            "curso_nombre",
            "curso_centro_id",
            "codigo_comision",
            "nombre",
            "cupo_total",
            "fecha_inicio",
            "fecha_fin",
            "estado",
            "observaciones",
            "fecha_creacion",
            "fecha_modificacion",
        ]


# ============================================================================
# FASE 4: OFERTA INSTITUCIONAL - COMISIONES
# ============================================================================


class ComisionHorarioSerializer(serializers.ModelSerializer):
    dia_nombre = serializers.CharField(source="dia_semana.nombre", read_only=True)

    class Meta:
        model = ComisionHorario
        fields = [
            "id",
            "comision",
            "dia_semana",
            "dia_nombre",
            "hora_desde",
            "hora_hasta",
            "aula_espacio",
            "vigente",
            "fecha_creacion",
            "fecha_modificacion",
        ]


class ComisionSerializer(serializers.ModelSerializer):
    horarios = ComisionHorarioSerializer(many=True, read_only=True)
    oferta_nombre = serializers.CharField(
        source="oferta.plan_curricular.titulo_referencia.nombre",
        read_only=True,
    )

    class Meta:
        model = Comision
        fields = [
            "id",
            "oferta",
            "oferta_nombre",
            "ubicacion",
            "codigo_comision",
            "nombre",
            "fecha_inicio",
            "fecha_fin",
            "cupo",
            "estado",
            "horarios",
            "observaciones",
            "fecha_creacion",
            "fecha_modificacion",
        ]


class OfertaInstitucionalSerializer(serializers.ModelSerializer):
    centro_nombre = serializers.CharField(source="centro.nombre", read_only=True)
    plan_nombre = serializers.CharField(
        source="plan_curricular.titulo_referencia.nombre", read_only=True
    )
    programa_nombre = serializers.CharField(source="programa.nombre", read_only=True)
    comisiones = ComisionSerializer(many=True, read_only=True)
    voucher_parametrias = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = OfertaInstitucional
        fields = [
            "id",
            "centro",
            "centro_nombre",
            "plan_curricular",
            "plan_nombre",
            "programa",
            "programa_nombre",
            "nombre_local",
            "ciclo_lectivo",
            "plan_externo_id",
            "estado",
            "costo",
            "usa_voucher",
            "voucher_parametrias",
            "fecha_publicacion",
            "comisiones",
            "observaciones",
            "fecha_creacion",
            "fecha_modificacion",
        ]


# ============================================================================
# FASE 5: INSCRIPCIÓN
# ============================================================================


class InscripcionSerializer(serializers.ModelSerializer):
    ciudadano_nombre = serializers.CharField(
        source="ciudadano.nombre_completo", read_only=True
    )
    comision_codigo = serializers.CharField(
        source="comision.codigo_comision", read_only=True
    )
    programa_nombre = serializers.CharField(source="programa.nombre", read_only=True)

    class Meta:
        model = Inscripcion
        fields = [
            "id",
            "ciudadano",
            "ciudadano_nombre",
            "comision",
            "comision_codigo",
            "programa",
            "programa_nombre",
            "estado",
            "origen_canal",
            "fecha_inscripcion",
            "fecha_validacion_presencial",
            "observaciones",
            "fecha_creacion",
            "fecha_modificacion",
        ]


# ============================================================================
# FASE 7: EVALUACIONES
# ============================================================================


class ResultadoEvaluacionSerializer(serializers.ModelSerializer):
    persona_nombre = serializers.CharField(
        source="inscripcion.ciudadano.nombre_completo", read_only=True
    )
    registrado_por_nombre = serializers.CharField(
        source="registrado_por.get_full_name", read_only=True
    )

    class Meta:
        model = ResultadoEvaluacion
        fields = [
            "id",
            "evaluacion",
            "inscripcion",
            "persona_nombre",
            "calificacion",
            "aprobo",
            "observaciones",
            "registrado_por",
            "registrado_por_nombre",
            "fecha_registro",
            "fecha_creacion",
            "fecha_modificacion",
        ]


class EvaluacionSerializer(serializers.ModelSerializer):
    comision_codigo = serializers.CharField(
        source="comision.codigo_comision", read_only=True
    )
    resultados = ResultadoEvaluacionSerializer(many=True, read_only=True)

    class Meta:
        model = Evaluacion
        fields = [
            "id",
            "comision",
            "comision_codigo",
            "tipo",
            "nombre",
            "descripcion",
            "fecha",
            "es_final",
            "ponderacion",
            "observaciones",
            "resultados",
            "fecha_creacion",
            "fecha_modificacion",
        ]


# ============================================================================
# VAT WEB API
# ============================================================================


class VatWebCentroSerializer(serializers.ModelSerializer):
    provincia_nombre = serializers.CharField(source="provincia.nombre", read_only=True)
    municipio_nombre = serializers.CharField(source="municipio.nombre", read_only=True)
    localidad_nombre = serializers.CharField(source="localidad.nombre", read_only=True)

    class Meta:
        model = Centro
        fields = [
            "id",
            "nombre",
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
            "correo",
        ]


class VatWebTituloSerializer(serializers.ModelSerializer):
    plan_estudio = serializers.IntegerField(source="plan_estudio_id", read_only=True)
    sector = serializers.IntegerField(source="plan_estudio.sector_id", read_only=True)
    sector_nombre = serializers.CharField(
        source="plan_estudio.sector.nombre", read_only=True
    )
    subsector = serializers.IntegerField(
        source="plan_estudio.subsector_id", read_only=True
    )
    subsector_nombre = serializers.CharField(
        source="plan_estudio.subsector.nombre", read_only=True
    )

    class Meta:
        model = TituloReferencia
        fields = [
            "id",
            "nombre",
            "codigo_referencia",
            "descripcion",
            "activo",
            "plan_estudio",
            "sector",
            "sector_nombre",
            "subsector",
            "subsector_nombre",
        ]


class VatWebCursoHorarioSerializer(serializers.ModelSerializer):
    dia_nombre = serializers.CharField(source="dia_semana.nombre", read_only=True)

    class Meta:
        model = ComisionHorario
        fields = [
            "id",
            "dia_semana",
            "dia_nombre",
            "hora_desde",
            "hora_hasta",
            "aula_espacio",
        ]


class VatWebCursoSerializer(serializers.ModelSerializer):
    centro_id = serializers.IntegerField(source="oferta.centro_id", read_only=True)
    centro_nombre = serializers.CharField(source="oferta.centro.nombre", read_only=True)
    titulo_id = serializers.IntegerField(
        source="oferta.plan_curricular.titulo_referencia_id", read_only=True
    )
    titulo_nombre = serializers.CharField(
        source="oferta.plan_curricular.titulo_referencia.nombre", read_only=True
    )
    plan_curricular_id = serializers.IntegerField(
        source="oferta.plan_curricular_id", read_only=True
    )
    plan_curricular_nombre = serializers.CharField(
        source="oferta.plan_curricular", read_only=True
    )
    programa_id = serializers.IntegerField(source="oferta.programa_id", read_only=True)
    programa_nombre = serializers.CharField(
        source="oferta.programa.nombre", read_only=True
    )
    ciclo_lectivo = serializers.IntegerField(
        source="oferta.ciclo_lectivo", read_only=True
    )
    costo = serializers.DecimalField(
        source="oferta.costo", max_digits=10, decimal_places=2, read_only=True
    )
    usa_voucher = serializers.BooleanField(source="oferta.usa_voucher", read_only=True)
    estado_oferta = serializers.CharField(source="oferta.estado", read_only=True)
    total_inscriptos = serializers.IntegerField(read_only=True)
    cupos_disponibles = serializers.SerializerMethodField()
    horarios = VatWebCursoHorarioSerializer(many=True, read_only=True)

    def get_cupos_disponibles(self, obj):
        total_inscriptos = getattr(obj, "total_inscriptos", 0) or 0
        return max(obj.cupo - total_inscriptos, 0)

    class Meta:
        model = Comision
        fields = [
            "id",
            "codigo_comision",
            "nombre",
            "estado",
            "estado_oferta",
            "fecha_inicio",
            "fecha_fin",
            "cupo",
            "total_inscriptos",
            "cupos_disponibles",
            "centro_id",
            "centro_nombre",
            "titulo_id",
            "titulo_nombre",
            "plan_curricular_id",
            "plan_curricular_nombre",
            "programa_id",
            "programa_nombre",
            "ciclo_lectivo",
            "costo",
            "usa_voucher",
            "observaciones",
            "horarios",
        ]


class VatWebInscripcionSerializer(serializers.ModelSerializer):
    ciudadano_nombre = serializers.CharField(
        source="ciudadano.nombre_completo", read_only=True
    )
    ciudadano_documento = serializers.IntegerField(
        source="ciudadano.documento", read_only=True
    )
    curso = VatWebCursoSerializer(source="comision", read_only=True)
    programa_nombre = serializers.CharField(source="programa.nombre", read_only=True)

    class Meta:
        model = Inscripcion
        fields = [
            "id",
            "ciudadano",
            "ciudadano_nombre",
            "ciudadano_documento",
            "comision",
            "curso",
            "programa",
            "programa_nombre",
            "estado",
            "origen_canal",
            "fecha_inscripcion",
            "fecha_validacion_presencial",
            "observaciones",
        ]


class VatWebInscripcionCreateSerializer(serializers.Serializer):
    ciudadano_id = serializers.IntegerField(required=False)
    documento = serializers.CharField(required=False)
    comision_id = serializers.IntegerField()
    estado = serializers.ChoiceField(
        choices=Inscripcion.ESTADO_INSCRIPCION_CHOICES,
        default="inscripta",
        required=False,
    )
    observaciones = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        ciudadano_id = attrs.get("ciudadano_id")
        documento = (attrs.get("documento") or "").strip()

        if not ciudadano_id and not documento:
            raise serializers.ValidationError("Debe enviar ciudadano_id o documento.")

        if ciudadano_id and documento:
            raise serializers.ValidationError(
                "Envíe ciudadano_id o documento, pero no ambos."
            )

        if ciudadano_id:
            ciudadano = Ciudadano.objects.filter(pk=ciudadano_id).first()
        else:
            if not documento.isdigit():
                raise serializers.ValidationError(
                    {"documento": "El documento debe ser numérico."}
                )
            ciudadano = Ciudadano.objects.filter(documento=int(documento)).first()

        if not ciudadano:
            raise serializers.ValidationError("No se encontró el ciudadano indicado.")

        comision = (
            Comision.objects.select_related("oferta__programa")
            .filter(pk=attrs["comision_id"])
            .first()
        )
        if not comision:
            raise serializers.ValidationError("No se encontró la comisión indicada.")

        if Inscripcion.objects.filter(ciudadano=ciudadano, comision=comision).exists():
            raise serializers.ValidationError(
                "El ciudadano ya tiene una inscripción en esta comisión."
            )

        attrs["ciudadano"] = ciudadano
        attrs["comision"] = comision
        attrs["programa"] = comision.oferta.programa
        return attrs

    def create(self, validated_data):
        from VAT.services.inscripcion_service import InscripcionService

        request = self.context.get("request")
        return InscripcionService.crear_inscripcion(
            ciudadano=validated_data["ciudadano"],
            comision=validated_data["comision"],
            programa=validated_data["programa"],
            estado=validated_data.get("estado", "inscripta"),
            origen_canal="api",
            observaciones=validated_data.get("observaciones", ""),
            usuario=getattr(request, "user", None),
        )

    def update(self, instance, validated_data):
        raise NotImplementedError(
            "VatWebInscripcionCreateSerializer solo soporta operaciones de creación."
        )
