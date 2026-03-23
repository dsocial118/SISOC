import logging

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

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
    InstitucionContacto,
    AutoridadInstitucional,
    InstitucionIdentificadorHist,
    InstitucionUbicacion,
    OfertaInstitucional,
    Comision,
    ComisionHorario,
    Inscripcion,
    Evaluacion,
    ResultadoEvaluacion,
)
from VAT.serializers import (
    CentroSerializer,
    ProvinciaSerializer,
    MunicipioSerializer,
    LocalidadSerializer,
    ModalidadInstitucionalSerializer,
    SectorSerializer,
    SubsectorSerializer,
    TituloReferenciaSerializer,
    ModalidadCursadaSerializer,
    PlanVersionCurricularSerializer,
    InscripcionOfertaSerializer,
    VoucherSerializer,
    InstitucionContactoSerializer,
    AutoridadInstitucionalSerializer,
    InstitucionIdentificadorHistSerializer,
    InstitucionUbicacionSerializer,
    OfertaInstitucionalSerializer,
    ComisionSerializer,
    ComisionHorarioSerializer,
    InscripcionSerializer,
    EvaluacionSerializer,
    ResultadoEvaluacionSerializer,
)
from core.api_auth import HasAPIKey
from core.models import Provincia, Municipio, Localidad
from core.soft_delete.view_helpers import is_soft_deletable_instance
from core.utils import format_serializer_errors

logger = logging.getLogger("django")


class SoftDeleteDestroyMixin:
    def perform_destroy(self, instance):
        if is_soft_deletable_instance(instance):
            user = (
                self.request.user
                if getattr(self.request.user, "is_authenticated", False)
                else None
            )
            instance.delete(user=user, cascade=True)
            return
        super().perform_destroy(instance)


@extend_schema(tags=["VAT - Centros"])
class CentroViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    queryset = Centro.objects.select_related(
        "referente", "provincia", "municipio", "localidad"
    ).order_by("id")
    serializer_class = CentroSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        activo = self.request.query_params.get("activo")
        if activo is not None:
            queryset = queryset.filter(activo=activo.lower() == "true")
        provincia_id = self.request.query_params.get("provincia_id")
        municipio_id = self.request.query_params.get("municipio_id")
        localidad_id = self.request.query_params.get("localidad_id")
        if provincia_id:
            queryset = queryset.filter(provincia_id=provincia_id)
        if municipio_id:
            queryset = queryset.filter(municipio_id=municipio_id)
        if localidad_id:
            queryset = queryset.filter(localidad_id=localidad_id)
        return queryset

    @action(detail=False, methods=["get"])
    def activos(self, request):
        centros = self.get_queryset().filter(activo=True)
        serializer = self.get_serializer(centros, many=True)
        return Response(serializer.data)


@extend_schema(tags=["VAT - Ubicación"])
class ProvinciaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Provincia.objects.all().order_by("nombre")
    serializer_class = ProvinciaSerializer
    permission_classes = [HasAPIKey]


@extend_schema(tags=["VAT - Ubicación"])
class MunicipioViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Municipio.objects.select_related("provincia").order_by("nombre")
    serializer_class = MunicipioSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        provincia_id = self.request.query_params.get("provincia_id")
        if provincia_id:
            queryset = queryset.filter(provincia_id=provincia_id)
        return queryset


@extend_schema(tags=["VAT - Ubicación"])
class LocalidadViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Localidad.objects.select_related("municipio__provincia").order_by(
        "nombre"
    )
    serializer_class = LocalidadSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        municipio_id = self.request.query_params.get("municipio_id")
        provincia_id = self.request.query_params.get("provincia_id")
        if municipio_id:
            queryset = queryset.filter(municipio_id=municipio_id)
        elif provincia_id:
            queryset = queryset.filter(municipio__provincia_id=provincia_id)
        return queryset


@extend_schema(tags=["VAT - Modalidades Institucionales"])
class ModalidadInstitucionalViewSet(viewsets.ModelViewSet):
    queryset = ModalidadInstitucional.objects.all().order_by("nombre")
    serializer_class = ModalidadInstitucionalSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        activo = self.request.query_params.get("activo")
        if activo is not None:
            queryset = queryset.filter(activo=activo.lower() == "true")
        return queryset


@extend_schema(tags=["VAT - Catálogos Académicos"])
class SectorViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    queryset = Sector.objects.all().order_by("nombre")
    serializer_class = SectorSerializer
    permission_classes = [HasAPIKey]


@extend_schema(tags=["VAT - Catálogos Académicos"])
class SubsectorViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    queryset = Subsector.objects.select_related("sector").order_by("sector", "nombre")
    serializer_class = SubsectorSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        sector_id = self.request.query_params.get("sector_id")
        if sector_id:
            queryset = queryset.filter(sector_id=sector_id)
        return queryset


@extend_schema(tags=["VAT - Catálogos Académicos"])
class TituloReferenciaViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    queryset = TituloReferencia.objects.select_related("sector", "subsector").order_by("nombre")
    serializer_class = TituloReferenciaSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        sector_id = self.request.query_params.get("sector_id")
        subsector_id = self.request.query_params.get("subsector_id")
        activo = self.request.query_params.get("activo")
        if sector_id:
            queryset = queryset.filter(sector_id=sector_id)
        if subsector_id:
            queryset = queryset.filter(subsector_id=subsector_id)
        if activo is not None:
            queryset = queryset.filter(activo=activo.lower() == "true")
        return queryset


@extend_schema(tags=["VAT - Catálogos Académicos"])
class ModalidadCursadaViewSet(viewsets.ModelViewSet):
    queryset = ModalidadCursada.objects.all().order_by("nombre")
    serializer_class = ModalidadCursadaSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        activo = self.request.query_params.get("activo")
        if activo is not None:
            queryset = queryset.filter(activo=activo.lower() == "true")
        return queryset


@extend_schema(tags=["VAT - Catálogos Académicos"])
class PlanVersionCurricularViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    queryset = PlanVersionCurricular.objects.select_related(
        "titulo_referencia", "modalidad_cursada"
    ).order_by("titulo_referencia", "modalidad_cursada")
    serializer_class = PlanVersionCurricularSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        titulo_referencia_id = self.request.query_params.get("titulo_referencia_id")
        modalidad_cursada_id = self.request.query_params.get("modalidad_cursada_id")
        activo = self.request.query_params.get("activo")
        if titulo_referencia_id:
            queryset = queryset.filter(titulo_referencia_id=titulo_referencia_id)
        if modalidad_cursada_id:
            queryset = queryset.filter(modalidad_cursada_id=modalidad_cursada_id)
        if activo is not None:
            queryset = queryset.filter(activo=activo.lower() == "true")
        return queryset


@extend_schema(tags=["VAT - Inscripciones"])
class InscripcionOfertaViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    queryset = InscripcionOferta.objects.select_related(
        "oferta", "ciudadano"
    ).order_by("-fecha_inscripcion")
    serializer_class = InscripcionOfertaSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        oferta_id = self.request.query_params.get("oferta_id")
        estado = self.request.query_params.get("estado")
        if oferta_id:
            queryset = queryset.filter(oferta_id=oferta_id)
        if estado:
            queryset = queryset.filter(estado=estado)
        return queryset


@extend_schema(tags=["VAT - Vouchers"])
class VoucherViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    """
    ViewSet for Voucher management.
    Supports filtering by ciudadano_id, estado, programa_id.
    """

    queryset = Voucher.objects.select_related(
        "ciudadano", "programa"
    ).prefetch_related("recargas", "usos").order_by("-fecha_asignacion")
    serializer_class = VoucherSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        ciudadano_id = self.request.query_params.get("ciudadano_id")
        estado = self.request.query_params.get("estado")
        programa_id = self.request.query_params.get("programa_id")

        if ciudadano_id:
            queryset = queryset.filter(ciudadano_id=ciudadano_id)
        if estado:
            queryset = queryset.filter(estado=estado)
        if programa_id:
            queryset = queryset.filter(programa_id=programa_id)

        return queryset

    @action(detail=True, methods=["get"])
    def disponible(self, request, pk=None):
        """Get available credit for a voucher."""
        voucher = self.get_object()
        return Response({
            "voucher_id": voucher.id,
            "cantidad_disponible": voucher.cantidad_disponible,
            "cantidad_usada": voucher.cantidad_usada,
            "cantidad_inicial": voucher.cantidad_inicial,
            "estado": voucher.estado,
        })

    @action(detail=False, methods=["get"])
    def por_ciudadano(self, request):
        """Get vouchers for a specific citizen."""
        ciudadano_id = request.query_params.get("ciudadano_id")
        if not ciudadano_id:
            return Response(
                {"error": "ciudadano_id es requerido"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        vouchers = self.queryset.filter(ciudadano_id=ciudadano_id)
        serializer = self.get_serializer(vouchers, many=True)
        return Response(serializer.data)


# Phase 2 - Institución (Institution-related ViewSets)

@extend_schema(tags=["VAT - Institución"])
class InstitucionContactoViewSet(viewsets.ModelViewSet):
    queryset = InstitucionContacto.objects.select_related("centro").order_by("tipo")
    serializer_class = InstitucionContactoSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        centro_id = self.request.query_params.get("centro_id")
        tipo = self.request.query_params.get("tipo")
        if centro_id:
            queryset = queryset.filter(centro_id=centro_id)
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        return queryset


@extend_schema(tags=["VAT - Institución"])
class AutoridadInstitucionalViewSet(viewsets.ModelViewSet):
    queryset = AutoridadInstitucional.objects.select_related("centro").order_by("cargo")
    serializer_class = AutoridadInstitucionalSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        centro_id = self.request.query_params.get("centro_id")
        if centro_id:
            queryset = queryset.filter(centro_id=centro_id)
        return queryset


@extend_schema(tags=["VAT - Institución"])
class InstitucionIdentificadorHistViewSet(viewsets.ModelViewSet):
    queryset = InstitucionIdentificadorHist.objects.select_related("centro").order_by("-vigencia_desde")
    serializer_class = InstitucionIdentificadorHistSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        centro_id = self.request.query_params.get("centro_id")
        tipo_identificador = self.request.query_params.get("tipo_identificador")
        if centro_id:
            queryset = queryset.filter(centro_id=centro_id)
        if tipo_identificador:
            queryset = queryset.filter(tipo_identificador=tipo_identificador)
        return queryset


@extend_schema(tags=["VAT - Institución"])
class InstitucionUbicacionViewSet(viewsets.ModelViewSet):
    queryset = InstitucionUbicacion.objects.select_related(
        "centro", "localidad"
    ).order_by("rol_ubicacion")
    serializer_class = InstitucionUbicacionSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        centro_id = self.request.query_params.get("centro_id")
        rol_ubicacion = self.request.query_params.get("rol_ubicacion")
        if centro_id:
            queryset = queryset.filter(centro_id=centro_id)
        if rol_ubicacion:
            queryset = queryset.filter(rol_ubicacion=rol_ubicacion)
        return queryset


# Phase 4 - Oferta Institucional

@extend_schema(tags=["VAT - Oferta Institucional"])
class OfertaInstitucionalViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    queryset = OfertaInstitucional.objects.select_related(
        "centro", "plan_curricular"
    ).order_by("-fecha_publicacion")
    serializer_class = OfertaInstitucionalSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        centro_id = self.request.query_params.get("centro_id")
        estado = self.request.query_params.get("estado")
        if centro_id:
            queryset = queryset.filter(centro_id=centro_id)
        if estado:
            queryset = queryset.filter(estado=estado)
        return queryset


@extend_schema(tags=["VAT - Oferta Institucional"])
class ComisionViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    queryset = Comision.objects.select_related(
        "oferta"
    ).prefetch_related("horarios").order_by("nombre")
    serializer_class = ComisionSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        oferta_id = self.request.query_params.get("oferta_id")
        estado = self.request.query_params.get("estado")
        if oferta_id:
            queryset = queryset.filter(oferta_id=oferta_id)
        if estado:
            queryset = queryset.filter(estado=estado)
        return queryset


@extend_schema(tags=["VAT - Oferta Institucional"])
class ComisionHorarioViewSet(viewsets.ModelViewSet):
    queryset = ComisionHorario.objects.select_related("comision").order_by("dia_semana", "hora_desde")
    serializer_class = ComisionHorarioSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        comision_id = self.request.query_params.get("comision_id")
        if comision_id:
            queryset = queryset.filter(comision_id=comision_id)
        return queryset


# Phase 5 - Inscripciones

@extend_schema(tags=["VAT - Inscripciones"])
class InscripcionViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    queryset = Inscripcion.objects.select_related(
        "ciudadano", "comision"
    ).order_by("-fecha_inscripcion")
    serializer_class = InscripcionSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        ciudadano_id = self.request.query_params.get("ciudadano_id")
        comision_id = self.request.query_params.get("comision_id")
        estado = self.request.query_params.get("estado")
        if ciudadano_id:
            queryset = queryset.filter(ciudadano_id=ciudadano_id)
        if comision_id:
            queryset = queryset.filter(comision_id=comision_id)
        if estado:
            queryset = queryset.filter(estado=estado)
        return queryset


# Phase 7 - Evaluaciones

@extend_schema(tags=["VAT - Evaluaciones"])
class EvaluacionViewSet(viewsets.ModelViewSet):
    queryset = Evaluacion.objects.select_related(
        "comision"
    ).prefetch_related("resultados").order_by("-fecha")
    serializer_class = EvaluacionSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        comision_id = self.request.query_params.get("comision_id")
        tipo = self.request.query_params.get("tipo")
        if comision_id:
            queryset = queryset.filter(comision_id=comision_id)
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        return queryset


@extend_schema(tags=["VAT - Evaluaciones"])
class ResultadoEvaluacionViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    queryset = ResultadoEvaluacion.objects.select_related("evaluacion").order_by("id")
    serializer_class = ResultadoEvaluacionSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        evaluacion_id = self.request.query_params.get("evaluacion_id")
        calificacion = self.request.query_params.get("calificacion")
        if evaluacion_id:
            queryset = queryset.filter(evaluacion_id=evaluacion_id)
        if calificacion:
            queryset = queryset.filter(calificacion=calificacion)
        return queryset
