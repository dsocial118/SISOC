import logging

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from VAT.models import (
    Centro,
    Categoria,
    Actividad,
    ActividadCentro,
    ParticipanteActividad,
    Beneficiario,
    Responsable,
    BeneficiarioResponsable,
    CabalArchivo,
    InformeCabalRegistro,
)
from VAT.serializers import (
    CentroSerializer,
    CategoriaSerializer,
    ActividadSerializer,
    ActividadCentroSerializer,
    ParticipanteActividadSerializer,
    BeneficiarioSerializer,
    ResponsableSerializer,
    BeneficiarioResponsableSerializer,
    CabalArchivoSerializer,
    InformeCabalRegistroSerializer,
    ProvinciaSerializer,
    MunicipioSerializer,
    LocalidadSerializer,
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


@extend_schema(tags=["VAT - Beneficiarios"])
class BeneficiarioViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    queryset = Beneficiario.objects.select_related(
        "responsable", "provincia", "municipio", "localidad"
    ).prefetch_related("actividades_detalle")
    serializer_class = BeneficiarioSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        responsable_id = self.request.query_params.get("responsable_id")
        dni = self.request.query_params.get("dni")
        if responsable_id:
            queryset = queryset.filter(responsable_id=responsable_id)
        if dni:
            queryset = queryset.filter(dni=dni)
        return queryset

    @action(detail=False, methods=["get"])
    def por_responsable(self, request):
        responsable_id = request.query_params.get("responsable_id")
        if not responsable_id:
            return Response(
                {"error": "responsable_id es requerido"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        beneficiarios = self.get_queryset().filter(responsable_id=responsable_id)
        serializer = self.get_serializer(beneficiarios, many=True)
        return Response(serializer.data)


@extend_schema(tags=["VAT - Responsables"])
class ResponsableViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    queryset = Responsable.objects.select_related("provincia", "municipio", "localidad")
    serializer_class = ResponsableSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        dni = self.request.query_params.get("dni")
        cuil = self.request.query_params.get("cuil")
        if dni:
            queryset = queryset.filter(dni=dni)
        if cuil:
            queryset = queryset.filter(cuil=cuil)
        return queryset


@extend_schema(tags=["VAT - Vínculos"])
class BeneficiarioResponsableViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    queryset = BeneficiarioResponsable.objects.select_related(
        "beneficiario", "responsable"
    ).order_by("id")
    serializer_class = BeneficiarioResponsableSerializer
    permission_classes = [HasAPIKey]


@extend_schema(tags=["VAT - Informes CABAL"])
class InformeCabalRegistroViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = InformeCabalRegistro.objects.select_related(
        "archivo", "centro"
    ).order_by("id")
    serializer_class = InformeCabalRegistroSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        archivo_id = self.request.query_params.get("archivo_id")
        centro_id = self.request.query_params.get("centro_id")
        no_coincidente = self.request.query_params.get("no_coincidente")
        if archivo_id:
            queryset = queryset.filter(archivo_id=archivo_id)
        if centro_id:
            queryset = queryset.filter(centro_id=centro_id)
        if no_coincidente is not None:
            queryset = queryset.filter(no_coincidente=no_coincidente.lower() == "true")
        return queryset

    @action(detail=False, methods=["get"])
    def por_centro(self, request):
        centro_id = request.query_params.get("centro_id")
        if not centro_id:
            return Response(
                {"error": "centro_id es requerido"}, status=status.HTTP_400_BAD_REQUEST
            )
        registros = self.get_queryset().filter(centro_id=centro_id)
        serializer = self.get_serializer(registros, many=True)
        return Response(serializer.data)


@extend_schema(tags=["VAT - Archivos CABAL"])
class CabalArchivoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        CabalArchivo.objects.select_related("usuario")
        .prefetch_related("registros")
        .order_by("id")
    )
    serializer_class = CabalArchivoSerializer
    permission_classes = [HasAPIKey]


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
