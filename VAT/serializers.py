# pylint: disable=too-many-lines

from datetime import date
import json

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers
from VAT.services.inscripcion_service import ESTADOS_INSCRIPCION_OCUPAN_CUPO
from VAT.models import (
    Centro,
    ModalidadInstitucional,
    Sector,
    Subsector,
    TituloReferencia,
    ModalidadCursada,
    PlanVersionCurricular,
    InscripcionOferta,
    VoucherParametria,
    Voucher,
    VoucherRecarga,
    VoucherUso,
    # Fase 2
    InstitucionContacto,
    InstitucionIdentificadorHist,
    InstitucionUbicacion,
    Curso,
    ComisionCurso,
    # Fase 4
    OfertaInstitucional,
    Comision,
    ComisionHorario,
    SesionComision,
    # Fase 5
    Inscripcion,
    SolicitudInscripcionPublica,
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
            "tipo_gestion",
            "clase_institucion",
            "situacion",
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
    titulo_referencia_nombre = serializers.CharField(source="nombre", read_only=True)
    sector_nombre = serializers.CharField(source="sector.nombre", read_only=True)
    subsector_nombre = serializers.CharField(source="subsector.nombre", read_only=True)
    modalidad_cursada_nombre = serializers.CharField(
        source="modalidad_cursada.nombre", read_only=True
    )

    class Meta:
        model = PlanVersionCurricular
        fields = [
            "id",
            "nombre",
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
            "nombre_contacto",
            "rol_area",
            "documento",
            "telefono_contacto",
            "email_contacto",
            "tipo",
            "valor",
            "es_principal",
            "observaciones",
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
            "nombre",
            "prioritario",
            "modalidad",
            "modalidad_nombre",
            "programa",
            "programa_nombre",
            "estado",
            "usa_voucher",
            "inscripcion_libre",
            "voucher_parametrias",
            "costo_creditos",
            "observaciones",
            "fecha_creacion",
            "fecha_modificacion",
        ]

    def validate(self, attrs):
        costo_creditos_default = Curso._meta.get_field("costo_creditos").get_default()
        curso = Curso(
            usa_voucher=attrs.get(
                "usa_voucher",
                getattr(self.instance, "usa_voucher", False),
            ),
            inscripcion_libre=attrs.get(
                "inscripcion_libre",
                getattr(self.instance, "inscripcion_libre", False),
            ),
            costo_creditos=attrs.get(
                "costo_creditos",
                getattr(self.instance, "costo_creditos", costo_creditos_default),
            ),
        )
        try:
            curso.clean()
        except DjangoValidationError as exc:
            detail = exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            raise serializers.ValidationError(detail) from exc

        attrs["costo_creditos"] = curso.costo_creditos
        return attrs


class ComisionCursoSerializer(serializers.ModelSerializer):
    class ComisionCursoHorarioReadSerializer(serializers.ModelSerializer):
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
                "vigente",
            ]

    class ComisionCursoSesionReadSerializer(serializers.ModelSerializer):
        dia_semana = serializers.IntegerField(
            source="horario.dia_semana_id", read_only=True
        )
        dia_nombre = serializers.CharField(
            source="horario.dia_semana.nombre", read_only=True
        )
        hora_desde = serializers.TimeField(source="horario.hora_desde", read_only=True)
        hora_hasta = serializers.TimeField(source="horario.hora_hasta", read_only=True)
        aula_espacio = serializers.CharField(
            source="horario.aula_espacio", read_only=True
        )

        class Meta:
            model = SesionComision
            fields = [
                "id",
                "horario",
                "numero_sesion",
                "fecha",
                "estado",
                "observaciones",
                "dia_semana",
                "dia_nombre",
                "hora_desde",
                "hora_hasta",
                "aula_espacio",
            ]

    curso_nombre = serializers.CharField(source="curso.nombre", read_only=True)
    curso_centro_id = serializers.IntegerField(source="curso.centro_id", read_only=True)
    ubicacion_nombre = serializers.CharField(
        source="ubicacion.nombre_ubicacion", read_only=True
    )
    horarios = ComisionCursoHorarioReadSerializer(many=True, read_only=True)
    sesiones = ComisionCursoSesionReadSerializer(many=True, read_only=True)

    class Meta:
        model = ComisionCurso
        fields = [
            "id",
            "curso",
            "curso_nombre",
            "curso_centro_id",
            "ubicacion",
            "ubicacion_nombre",
            "codigo_comision",
            "nombre",
            "cupo_total",
            "acepta_lista_espera",
            "fecha_inicio",
            "fecha_fin",
            "estado",
            "horarios",
            "sesiones",
            "observaciones",
            "fecha_creacion",
            "fecha_modificacion",
        ]


class CursoBusquedaVoucherParametriaSerializer(serializers.ModelSerializer):
    programa_nombre = serializers.CharField(source="programa.nombre", read_only=True)

    class Meta:
        model = VoucherParametria
        fields = [
            "id",
            "nombre",
            "programa",
            "programa_nombre",
            "cantidad_inicial",
            "fecha_vencimiento",
            "inscripcion_unica_activa",
            "activa",
        ]


class CursoBusquedaCiudadSerializer(serializers.Serializer):
    provincia = ProvinciaSerializer(read_only=True)
    municipio = MunicipioSerializer(read_only=True)
    localidad = LocalidadSerializer(read_only=True)
    direccion = serializers.CharField(source="domicilio_actividad", read_only=True)

    def create(self, validated_data):
        return validated_data

    def update(self, instance, validated_data):
        return instance


class CursoBusquedaCentroSerializer(serializers.ModelSerializer):
    referente_nombre = serializers.CharField(
        source="referente.get_full_name", read_only=True
    )
    provincia = ProvinciaSerializer(read_only=True)
    ciudad = CursoBusquedaCiudadSerializer(source="*", read_only=True)

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
            "ciudad",
            "telefono",
            "celular",
            "correo",
            "nombre_referente",
            "apellido_referente",
            "tipo_gestion",
            "clase_institucion",
            "situacion",
        ]


class CursoBusquedaUbicacionSerializer(serializers.ModelSerializer):
    localidad_nombre = serializers.CharField(source="localidad.nombre", read_only=True)
    municipio_id = serializers.IntegerField(
        source="localidad.municipio_id", read_only=True
    )
    municipio_nombre = serializers.CharField(
        source="localidad.municipio.nombre", read_only=True
    )
    provincia_id = serializers.IntegerField(
        source="localidad.municipio.provincia_id", read_only=True
    )
    provincia_nombre = serializers.CharField(
        source="localidad.municipio.provincia.nombre", read_only=True
    )

    class Meta:
        model = InstitucionUbicacion
        fields = [
            "id",
            "rol_ubicacion",
            "nombre_ubicacion",
            "domicilio",
            "es_principal",
            "localidad",
            "localidad_nombre",
            "municipio_id",
            "municipio_nombre",
            "provincia_id",
            "provincia_nombre",
        ]


class CursoBusquedaComisionSerializer(serializers.ModelSerializer):
    horarios = ComisionCursoSerializer.ComisionCursoHorarioReadSerializer(
        many=True, read_only=True
    )
    sesiones = ComisionCursoSerializer.ComisionCursoSesionReadSerializer(
        many=True, read_only=True
    )
    ubicacion = CursoBusquedaUbicacionSerializer(read_only=True)
    total_inscriptos = serializers.SerializerMethodField()
    cupos_disponibles = serializers.SerializerMethodField()

    def get_total_inscriptos(self, obj):
        total_inscriptos = getattr(obj, "total_inscriptos", None)
        if total_inscriptos is not None:
            return total_inscriptos
        if hasattr(obj, "inscripciones_prefetch"):
            return len(
                [
                    inscripcion
                    for inscripcion in obj.inscripciones_prefetch
                    if inscripcion.estado in ESTADOS_INSCRIPCION_OCUPAN_CUPO
                ]
            )
        return obj.inscripciones.filter(
            estado__in=ESTADOS_INSCRIPCION_OCUPAN_CUPO
        ).count()

    def get_cupos_disponibles(self, obj):
        total_inscriptos = self.get_total_inscriptos(obj) or 0
        return max((obj.cupo_total or 0) - total_inscriptos, 0)

    class Meta:
        model = ComisionCurso
        fields = [
            "id",
            "codigo_comision",
            "nombre",
            "estado",
            "acepta_lista_espera",
            "cupo_total",
            "total_inscriptos",
            "cupos_disponibles",
            "fecha_inicio",
            "fecha_fin",
            "observaciones",
            "ubicacion",
            "horarios",
            "sesiones",
            "fecha_creacion",
            "fecha_modificacion",
        ]


class CursoBusquedaSerializer(serializers.ModelSerializer):
    centro = CursoBusquedaCentroSerializer(read_only=True)
    plan_estudio_nombre = serializers.CharField(source="plan_estudio", read_only=True)
    modalidad_nombre = serializers.CharField(source="modalidad.nombre", read_only=True)
    programa = serializers.SerializerMethodField()
    voucher_parametrias = CursoBusquedaVoucherParametriaSerializer(
        many=True, read_only=True
    )
    comisiones = CursoBusquedaComisionSerializer(many=True, read_only=True)

    def get_programa(self, obj):
        programa = obj.programa
        if programa is None:
            return None
        return {
            "id": programa.id,
            "nombre": programa.nombre,
        }

    class Meta:
        model = Curso
        fields = [
            "id",
            "nombre",
            "prioritario",
            "estado",
            "observaciones",
            "fecha_creacion",
            "fecha_modificacion",
            "usa_voucher",
            "inscripcion_libre",
            "costo_creditos",
            "centro",
            "plan_estudio",
            "plan_estudio_nombre",
            "modalidad",
            "modalidad_nombre",
            "programa",
            "voucher_parametrias",
            "comisiones",
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
            "acepta_lista_espera",
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
    comision_codigo = serializers.SerializerMethodField()
    comision_curso_codigo = serializers.CharField(
        source="comision_curso.codigo_comision", read_only=True
    )
    entidad_comision_tipo = serializers.SerializerMethodField()
    programa_nombre = serializers.CharField(source="programa.nombre", read_only=True)

    def get_comision_codigo(self, obj):
        entidad = obj.entidad_comision
        return entidad.codigo_comision if entidad else None

    def get_entidad_comision_tipo(self, obj):
        if obj.comision_curso_id:
            return "comision_curso"
        if obj.comision_id:
            return "comision"
        return None

    def validate(self, attrs):
        comision = attrs.get("comision", getattr(self.instance, "comision", None))
        comision_curso = attrs.get(
            "comision_curso",
            getattr(self.instance, "comision_curso", None),
        )

        if bool(comision) == bool(comision_curso):
            raise serializers.ValidationError(
                "Debe enviar una comisión de oferta o una comisión de curso."
            )

        return attrs

    class Meta:
        model = Inscripcion
        fields = [
            "id",
            "ciudadano",
            "ciudadano_nombre",
            "comision",
            "comision_codigo",
            "comision_curso",
            "comision_curso_codigo",
            "entidad_comision_tipo",
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
        validators = []
        extra_kwargs = {
            "comision": {"required": False},
            "comision_curso": {"required": False},
            "programa": {"required": False},
        }


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
    centro_id = serializers.IntegerField(source="curso.centro_id", read_only=True)
    centro_nombre = serializers.CharField(source="curso.centro.nombre", read_only=True)
    titulo_id = serializers.SerializerMethodField()
    titulo_nombre = serializers.SerializerMethodField()
    plan_curricular_id = serializers.IntegerField(
        source="curso.plan_estudio_id", read_only=True
    )
    plan_curricular_nombre = serializers.CharField(
        source="curso.plan_estudio", read_only=True
    )
    programa_id = serializers.IntegerField(source="curso.programa_id", read_only=True)
    programa_nombre = serializers.CharField(
        source="curso.programa.nombre", read_only=True
    )
    ciclo_lectivo = serializers.SerializerMethodField()
    costo = serializers.IntegerField(read_only=True)
    usa_voucher = serializers.BooleanField(source="curso.usa_voucher", read_only=True)
    inscripcion_libre = serializers.BooleanField(
        source="curso.inscripcion_libre", read_only=True
    )
    acepta_lista_espera = serializers.BooleanField(read_only=True)
    estado_oferta = serializers.CharField(source="curso.estado", read_only=True)
    estado_curso = serializers.CharField(source="curso.estado", read_only=True)
    cupo = serializers.IntegerField(source="cupo_total", read_only=True)
    total_inscriptos = serializers.SerializerMethodField()
    cupos_disponibles = serializers.SerializerMethodField()
    horarios = VatWebCursoHorarioSerializer(many=True, read_only=True)

    def get_titulo_id(self, obj):
        plan_estudio = getattr(obj.curso, "plan_estudio", None)
        return plan_estudio.titulo_referencia_id if plan_estudio else None

    def get_titulo_nombre(self, obj):
        plan_estudio = getattr(obj.curso, "plan_estudio", None)
        if not plan_estudio:
            return None
        titulo_referencia = plan_estudio.titulo_referencia
        if titulo_referencia:
            return titulo_referencia.nombre
        nombre = (plan_estudio.nombre or "").strip()
        return nombre or None

    def get_ciclo_lectivo(self, obj):
        return obj.fecha_inicio.year if obj.fecha_inicio else None

    def get_total_inscriptos(self, obj):
        total_inscriptos = getattr(obj, "total_inscriptos", None)
        if total_inscriptos is not None:
            return total_inscriptos
        return obj.inscripciones.filter(
            estado__in=ESTADOS_INSCRIPCION_OCUPAN_CUPO
        ).count()

    def get_cupos_disponibles(self, obj):
        total_inscriptos = self.get_total_inscriptos(obj) or 0
        return max(obj.cupo_total - total_inscriptos, 0)

    class Meta:
        model = ComisionCurso
        fields = [
            "id",
            "codigo_comision",
            "nombre",
            "estado",
            "estado_oferta",
            "estado_curso",
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
            "inscripcion_libre",
            "acepta_lista_espera",
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
    comision = serializers.IntegerField(source="comision_curso_id", read_only=True)
    comision_curso = serializers.IntegerField(
        source="comision_curso_id", read_only=True
    )
    curso = VatWebCursoSerializer(source="comision_curso", read_only=True)
    programa_nombre = serializers.CharField(
        source="programa.nombre", read_only=True, allow_null=True
    )
    estado_nombre = serializers.CharField(source="get_estado_display", read_only=True)
    en_lista_espera = serializers.SerializerMethodField()

    def get_en_lista_espera(self, obj):
        return obj.estado == "en_espera"

    class Meta:
        model = Inscripcion
        fields = [
            "id",
            "ciudadano",
            "ciudadano_nombre",
            "ciudadano_documento",
            "comision",
            "comision_curso",
            "curso",
            "programa",
            "programa_nombre",
            "estado",
            "estado_nombre",
            "en_lista_espera",
            "origen_canal",
            "fecha_inscripcion",
            "fecha_validacion_presencial",
            "observaciones",
        ]


def _resolver_entidad_comision_vat_web_inscripcion(attrs):
    comision_curso_id = attrs.get("comision_curso_id")
    comision_id = attrs.get("comision_id")

    if not comision_curso_id and not comision_id:
        raise serializers.ValidationError(
            "Debe enviar comision_curso_id o comision_id."
        )

    if comision_curso_id and comision_id and comision_curso_id != comision_id:
        raise serializers.ValidationError(
            "Si envía comision_id y comision_curso_id deben referir a la misma comisión de curso."
        )

    entidad_comision = None
    if comision_curso_id:
        entidad_comision = (
            ComisionCurso.objects.select_related("curso", "curso__centro")
            .filter(pk=comision_curso_id)
            .first()
        )
    elif comision_id:
        entidad_comision = (
            Comision.objects.select_related("oferta", "oferta__centro")
            .filter(pk=comision_id)
            .first()
        )

    if not entidad_comision:
        raise serializers.ValidationError(
            "No se encontró la comisión o comisión de curso indicada."
        )

    return entidad_comision


def _extraer_datos_postulante(attrs):
    datos_postulante = attrs.get("datos_postulante")
    if isinstance(datos_postulante, dict):
        return datos_postulante

    observaciones = attrs.get("observaciones")
    if not isinstance(observaciones, str):
        return None

    observaciones = observaciones.strip()
    if not observaciones:
        return None

    try:
        parsed = json.loads(observaciones)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None

    return parsed if isinstance(parsed, dict) else None


def _completar_documento_postulante(datos_postulante, documento_principal):
    if not isinstance(datos_postulante, dict):
        return datos_postulante

    documento_principal = str(documento_principal or "").strip()
    if not documento_principal:
        return datos_postulante

    if str(datos_postulante.get("documento") or "").strip():
        return datos_postulante

    datos_postulante_normalizado = dict(datos_postulante)
    datos_postulante_normalizado["documento"] = documento_principal
    return datos_postulante_normalizado


def _raise_datos_postulante_error(detail):
    raise serializers.ValidationError({"datos_postulante": detail})


def _normalizar_documento_postulante(datos_postulante):
    documento_explicitado = str(datos_postulante.get("documento") or "").strip()
    cuil = str(datos_postulante.get("cuil") or "").strip()
    usa_cuil_como_documento = not documento_explicitado and bool(cuil)
    documento = documento_explicitado or cuil
    if usa_cuil_como_documento:
        documento = "".join(caracter for caracter in documento if caracter.isdigit())
    return documento, usa_cuil_como_documento


def _resolver_tipo_documento_postulante(datos_postulante):
    tipo_documento = (
        datos_postulante.get("tipo_documento") or Ciudadano.DOCUMENTO_DNI
    ).strip()
    tipos_validos = {valor for valor, _ in Ciudadano.DOCUMENTO_CHOICES}
    if tipo_documento in tipos_validos:
        return tipo_documento
    return Ciudadano.DOCUMENTO_DNI


def _resolver_identidad_postulante(datos_postulante):
    nombre = (datos_postulante.get("nombre") or "").strip()
    apellido = (datos_postulante.get("apellido") or "").strip()
    documento, usa_cuil_como_documento = _normalizar_documento_postulante(
        datos_postulante
    )
    _validar_datos_postulante(nombre, apellido, documento)

    return {
        "nombre": nombre,
        "apellido": apellido,
        "documento": documento,
        "tipo_documento": _resolver_tipo_documento_postulante(datos_postulante),
        "usa_cuil_como_documento": usa_cuil_como_documento,
    }


def _validar_datos_postulante(nombre, apellido, documento):
    errores = {}
    if not nombre:
        errores["nombre"] = "Debe informar el nombre del postulante."
    if not apellido:
        errores["apellido"] = "Debe informar el apellido del postulante."
    if not documento:
        errores["documento"] = "Debe informar el documento o cuil del postulante."
    elif not documento.isdigit():
        errores["documento"] = "El documento del postulante debe ser numérico."

    if errores:
        _raise_datos_postulante_error(errores)


def _resolver_fecha_nacimiento_postulante(datos_postulante):
    fecha_nacimiento_raw = datos_postulante.get("fecha_nacimiento")
    if not fecha_nacimiento_raw:
        return (
            date(1900, 1, 1),
            [
                "Fecha de nacimiento no informada; se asignó 1900-01-01 para "
                "habilitar la inscripción operativa."
            ],
        )

    try:
        fecha_nacimiento = serializers.DateField().run_validation(fecha_nacimiento_raw)
    except serializers.ValidationError as exc:
        _raise_datos_postulante_error({"fecha_nacimiento": exc.detail})

    return fecha_nacimiento, []


def _resolver_o_crear_ciudadano_desde_datos_postulante(datos_postulante, usuario=None):
    if not isinstance(datos_postulante, dict):
        _raise_datos_postulante_error(
            "Debe enviar un objeto con los datos del postulante."
        )

    identidad = _resolver_identidad_postulante(datos_postulante)
    documento_int = int(identidad["documento"])
    ciudadano_existente = Ciudadano.objects.filter(
        tipo_documento=identidad["tipo_documento"],
        documento=documento_int,
    ).first()
    if ciudadano_existente:
        return ciudadano_existente

    fecha_nacimiento, observaciones_adicionales = _resolver_fecha_nacimiento_postulante(
        datos_postulante
    )
    observaciones = ["Ciudadano creado automáticamente desde inscripción libre web."]
    observaciones.extend(observaciones_adicionales)
    if identidad["usa_cuil_como_documento"]:
        observaciones.append(
            "Se tomó el CUIL informado como documento para el alta automática."
        )

    usuario_auditoria = usuario if getattr(usuario, "is_authenticated", False) else None

    return Ciudadano.objects.create(
        apellido=identidad["apellido"],
        nombre=identidad["nombre"],
        fecha_nacimiento=fecha_nacimiento,
        tipo_documento=identidad["tipo_documento"],
        documento=documento_int,
        telefono=(datos_postulante.get("telefono") or "").strip() or None,
        email=(datos_postulante.get("email") or "").strip() or None,
        origen_dato="manual",
        observaciones=" ".join(observaciones),
        creado_por=usuario_auditoria,
        modificado_por=usuario_auditoria,
    )


def _resolver_referencias_vat_web_inscripcion(attrs):
    ciudadano_id = attrs.get("ciudadano_id")
    documento = (attrs.get("documento") or "").strip()
    datos_postulante = _extraer_datos_postulante(attrs)
    datos_postulante = _completar_documento_postulante(datos_postulante, documento)
    entidad_comision = _resolver_entidad_comision_vat_web_inscripcion(attrs)
    permite_solicitud_publica = bool(
        getattr(getattr(entidad_comision, "curso", None), "inscripcion_libre", False)
    )

    if not ciudadano_id and not documento and not datos_postulante:
        raise serializers.ValidationError(
            "Debe enviar ciudadano_id, documento o datos_postulante."
        )

    if ciudadano_id and documento:
        raise serializers.ValidationError(
            "Envíe ciudadano_id o documento, pero no ambos."
        )

    if ciudadano_id:
        ciudadano = Ciudadano.objects.filter(pk=ciudadano_id).first()
    elif documento:
        if not documento.isdigit():
            raise serializers.ValidationError(
                {"documento": "El documento debe ser numérico."}
            )
        ciudadano = Ciudadano.objects.filter(documento=int(documento)).first()
    else:
        ciudadano = None

    if not ciudadano and not (permite_solicitud_publica and datos_postulante):
        raise serializers.ValidationError("No se encontró el ciudadano indicado.")

    return ciudadano, entidad_comision, datos_postulante


def _resolver_programa_vat_web(comision):
    programa = getattr(comision, "programa", None)
    if programa is not None:
        return programa

    oferta = getattr(comision, "oferta", None)
    return getattr(oferta, "programa", None)


class VatPlainSerializer(serializers.Serializer):
    def create(self, validated_data):
        return validated_data

    def update(self, instance, validated_data):
        return instance


class VatWebInscripcionBaseSerializer(VatPlainSerializer):
    ciudadano_id = serializers.IntegerField(required=False)
    documento = serializers.CharField(required=False)
    comision_id = serializers.IntegerField(required=False)
    comision_curso_id = serializers.IntegerField(required=False)

    def validate(self, attrs):
        ciudadano, comision, datos_postulante = (
            _resolver_referencias_vat_web_inscripcion(attrs)
        )
        attrs["ciudadano"] = ciudadano
        attrs["comision_curso"] = comision
        attrs["programa"] = _resolver_programa_vat_web(comision)
        if datos_postulante:
            attrs["datos_postulante"] = datos_postulante
        return attrs


class VatWebInscripcionPrevalidacionSerializer(VatWebInscripcionBaseSerializer):
    cuil = serializers.CharField(required=False, allow_blank=True)


class VatWebInscripcionPrevalidacionCiudadanoSerializer(VatPlainSerializer):
    id = serializers.IntegerField()
    documento = serializers.IntegerField()
    nombre = serializers.CharField()


class VatWebInscripcionPrevalidacionComisionSerializer(VatPlainSerializer):
    id = serializers.IntegerField()
    codigo_comision = serializers.CharField()
    nombre = serializers.CharField()
    estado = serializers.CharField()
    curso_id = serializers.IntegerField()
    curso_nombre = serializers.CharField()
    centro_id = serializers.IntegerField()
    centro_nombre = serializers.CharField()
    programa_id = serializers.IntegerField(allow_null=True)
    programa_nombre = serializers.CharField(allow_null=True)
    usa_voucher = serializers.BooleanField()
    inscripcion_libre = serializers.BooleanField()
    acepta_lista_espera = serializers.BooleanField()
    ingresa_a_lista_espera = serializers.BooleanField()
    cupo_total = serializers.IntegerField()
    cupos_disponibles = serializers.IntegerField()
    costo = serializers.IntegerField()


class VatWebInscripcionPrevalidacionVoucherSerializer(VatPlainSerializer):
    requerido = serializers.BooleanField()
    programa_id = serializers.IntegerField(allow_null=True)
    programa_nombre = serializers.CharField(allow_null=True)
    parametrias_habilitadas = serializers.ListField(
        child=serializers.IntegerField(),
    )
    voucher_id = serializers.IntegerField(allow_null=True)
    parametria_id = serializers.IntegerField(allow_null=True)
    saldo_actual = serializers.IntegerField(allow_null=True)
    credito_requerido = serializers.IntegerField(allow_null=True)
    saldo_post_inscripcion = serializers.IntegerField(allow_null=True)


class VatWebInscripcionPrevalidacionResponseSerializer(VatPlainSerializer):
    puede_inscribirse = serializers.BooleanField()
    motivos = serializers.ListField(child=serializers.CharField())
    ciudadano = VatWebInscripcionPrevalidacionCiudadanoSerializer()
    comision = VatWebInscripcionPrevalidacionComisionSerializer()
    voucher = VatWebInscripcionPrevalidacionVoucherSerializer()


class VatWebSolicitudInscripcionPublicaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SolicitudInscripcionPublica
        fields = [
            "id",
            "ciudadano",
            "comision_curso",
            "programa",
            "inscripcion",
            "estado",
            "origen_canal",
            "datos_postulante",
            "observaciones",
            "fecha_creacion",
            "fecha_modificacion",
        ]


class VatWebInscripcionCreateSerializer(VatWebInscripcionBaseSerializer):
    estado = serializers.ChoiceField(
        choices=Inscripcion.ESTADO_INSCRIPCION_CHOICES,
        default="inscripta",
        required=False,
    )
    observaciones = serializers.CharField(required=False, allow_blank=True)
    datos_postulante = serializers.JSONField(required=False)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        ciudadano = attrs["ciudadano"]
        comision = attrs["comision_curso"]

        if ciudadano is None:
            if not getattr(comision.curso, "inscripcion_libre", False):
                raise serializers.ValidationError(
                    "La comisión indicada no admite solicitudes públicas sin ciudadano."
                )
            return attrs

        if Inscripcion.objects.filter(
            ciudadano=ciudadano,
            **(
                {"comision": comision}
                if getattr(comision, "oferta_id", None)
                else {"comision_curso": comision}
            ),
        ).exists():
            raise serializers.ValidationError(
                "El ciudadano ya tiene una inscripción en esta comisión."
            )

        attrs["ciudadano"] = ciudadano
        attrs["comision_curso"] = comision
        attrs["programa"] = _resolver_programa_vat_web(comision)
        return attrs

    def create(self, validated_data):
        from VAT.services.inscripcion_service import InscripcionService
        from VAT.services.solicitud_inscripcion_publica_service import (
            SolicitudInscripcionPublicaService,
        )

        request = self.context.get("request")

        if validated_data.get("ciudadano") is None:
            with transaction.atomic():
                ciudadano = _resolver_o_crear_ciudadano_desde_datos_postulante(
                    validated_data.get("datos_postulante") or {},
                    usuario=getattr(request, "user", None),
                )
                inscripcion = InscripcionService.crear_inscripcion(
                    ciudadano=ciudadano,
                    comision=validated_data["comision_curso"],
                    programa=validated_data.get("programa"),
                    estado=validated_data.get("estado", "inscripta"),
                    origen_canal="front_publico",
                    observaciones=validated_data.get("observaciones", ""),
                    usuario=getattr(request, "user", None),
                )
                SolicitudInscripcionPublicaService.registrar_conversion_desde_vat_web(
                    comision=validated_data["comision_curso"],
                    ciudadano=ciudadano,
                    inscripcion=inscripcion,
                    programa=validated_data.get("programa"),
                    datos_postulante=validated_data.get("datos_postulante") or {},
                    observaciones=validated_data.get("observaciones", ""),
                )
            return inscripcion

        return InscripcionService.crear_inscripcion(
            ciudadano=validated_data["ciudadano"],
            comision=validated_data["comision_curso"],
            programa=validated_data["programa"],
            estado=validated_data.get("estado", "inscripta"),
            origen_canal="front_publico",
            observaciones=validated_data.get("observaciones", ""),
            usuario=getattr(request, "user", None),
        )

    def update(self, instance, validated_data):
        raise NotImplementedError(
            "VatWebInscripcionCreateSerializer solo soporta operaciones de creación."
        )
