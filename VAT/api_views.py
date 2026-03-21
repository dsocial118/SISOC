import logging

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from VAT.models import (
    Centro,
    Categoria,
    Actividad,
    ActividadCentro,
    ParticipanteActividad,
    ModalidadInstitucional,
    Sector,
    Subsector,
    TituloReferencia,
    ModalidadCursada,
    PlanVersionCurricular,
)
from VAT.serializers import (
    CentroSerializer,
    CategoriaSerializer,
    ActividadSerializer,
    ActividadCentroSerializer,
    ParticipanteActividadSerializer,
    ProvinciaSerializer,
    MunicipioSerializer,
    LocalidadSerializer,
    ModalidadInstitucionalSerializer,
    SectorSerializer,
    SubsectorSerializer,
    TituloReferenciaSerializer,
    ModalidadCursadaSerializer,
    PlanVersionCurricularSerializer,
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
        categoria_id = self.request.query_params.get("categoria_id")
        if categoria_id:
            queryset = queryset.filter(
                actividadcentro__actividad__categoria_id=categoria_id
            ).distinct()
        return queryset

    @action(detail=False, methods=["get"])
    def activos(self, request):
        centros = self.get_queryset().filter(activo=True)
        serializer = self.get_serializer(centros, many=True)
        return Response(serializer.data)


@extend_schema(tags=["VAT - Actividades"])
class ActividadViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    queryset = Actividad.objects.select_related("categoria").order_by("id")
    serializer_class = ActividadSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        categoria_id = self.request.query_params.get("categoria_id")
        if categoria_id:
            queryset = queryset.filter(categoria_id=categoria_id)
        return queryset


@extend_schema(tags=["VAT - Categorías"])
class CategoriaViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    queryset = Categoria.objects.all().order_by("id")
    serializer_class = CategoriaSerializer
    permission_classes = [HasAPIKey]


@extend_schema(tags=["VAT - Actividades por Centro"])
class ActividadCentroViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    queryset = (
        ActividadCentro.objects.select_related(
            "centro", "actividad", "actividad__categoria"
        )
        .prefetch_related("dias", "sexoact")
        .order_by("id")
    )
    serializer_class = ActividadCentroSerializer
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

    @action(detail=False, methods=["get"])
    def por_centro(self, request):
        centro_id = request.query_params.get("centro_id")
        if not centro_id:
            return Response(
                {"error": "centro_id es requerido"}, status=status.HTTP_400_BAD_REQUEST
            )
        actividades = self.queryset.filter(centro_id=centro_id)
        estado = request.query_params.get("estado")
        if estado:
            actividades = actividades.filter(estado=estado)
        serializer = self.get_serializer(actividades, many=True)
        return Response(serializer.data)


@extend_schema(tags=["VAT - Participantes"])
class ParticipanteActividadViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    queryset = (
        ParticipanteActividad.objects.select_related("actividad_centro", "ciudadano")
        .prefetch_related("historial")
        .order_by("id")
    )
    serializer_class = ParticipanteActividadSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        actividad_centro_id = self.request.query_params.get("actividad_centro_id")
        estado = self.request.query_params.get("estado")
        if actividad_centro_id:
            queryset = queryset.filter(actividad_centro_id=actividad_centro_id)
        if estado:
            queryset = queryset.filter(estado=estado)
        return queryset

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                error_msg = format_serializer_errors(serializer)
                return Response(
                    {"error": error_msg}, status=status.HTTP_400_BAD_REQUEST
                )
        except Exception:
            logger.exception("Error al inscribir participante")
            return Response(
                {
                    "error": "Ocurrió un error interno. Por favor, inténtelo de nuevo más tarde."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["post"])
    def cambiar_estado(self, request, pk=None):
        participante = self.get_object()
        nuevo_estado = request.data.get("estado")
        if nuevo_estado not in dict(ParticipanteActividad.ESTADO_INSCRIPCION):
            return Response(
                {"error": "Estado inválido"}, status=status.HTTP_400_BAD_REQUEST
            )
        participante.estado = nuevo_estado
        participante.save()
        serializer = self.get_serializer(participante)
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
