import logging

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from centrodefamilia.models import (
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
from centrodefamilia.serializers import (
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
)
from core.api_auth import IsInApiCentroFamiliaGroup
from core.utils import format_serializer_errors

logger = logging.getLogger("django")


class CentroViewSet(viewsets.ModelViewSet):
    """
    API para gestionar Centros de Familia.
    - GET /api/centros/ - Listar centros
    - POST /api/centros/ - Crear centro
    - GET /api/centros/{id}/ - Detalle del centro
    - PUT /api/centros/{id}/ - Actualizar centro
    - DELETE /api/centros/{id}/ - Eliminar centro
    """

    queryset = Centro.objects.select_related(
        "referente", "provincia", "municipio", "localidad"
    )
    serializer_class = CentroSerializer
    permission_classes = [IsInApiCentroFamiliaGroup]

    def get_queryset(self):
        queryset = super().get_queryset()
        activo = self.request.query_params.get("activo")
        if activo is not None:
            queryset = queryset.filter(activo=activo.lower() == "true")
        return queryset

    @action(detail=False, methods=["get"])
    def activos(self, request):
        """Listar solo centros activos"""
        centros = self.get_queryset().filter(activo=True)
        serializer = self.get_serializer(centros, many=True)
        return Response(serializer.data)


class ActividadViewSet(viewsets.ModelViewSet):
    """
    API para gestionar Actividades.
    - GET /api/actividades/ - Listar actividades
    - POST /api/actividades/ - Crear actividad
    - GET /api/actividades/{id}/ - Detalle
    """

    queryset = Actividad.objects.select_related("categoria")
    serializer_class = ActividadSerializer
    permission_classes = [IsInApiCentroFamiliaGroup]

    def get_queryset(self):
        queryset = super().get_queryset()
        categoria_id = self.request.query_params.get("categoria_id")
        if categoria_id:
            queryset = queryset.filter(categoria_id=categoria_id)
        return queryset


class CategoriaViewSet(viewsets.ModelViewSet):
    """API para gestionar Categorías de Actividades"""

    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [IsInApiCentroFamiliaGroup]


class ActividadCentroViewSet(viewsets.ModelViewSet):
    """
    API para gestionar Actividades por Centro.
    - GET /api/actividades-centro/ - Listar
    - POST /api/actividades-centro/ - Crear
    - GET /api/actividades-centro/{id}/ - Detalle
    """

    queryset = ActividadCentro.objects.select_related(
        "centro", "actividad", "actividad__categoria"
    ).prefetch_related("dias", "sexoact")
    serializer_class = ActividadCentroSerializer
    permission_classes = [IsInApiCentroFamiliaGroup]

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
        """Listar actividades de un centro específico"""
        centro_id = request.query_params.get("centro_id")
        if not centro_id:
            return Response(
                {"error": "centro_id es requerido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        actividades = self.get_queryset().filter(centro_id=centro_id)
        serializer = self.get_serializer(actividades, many=True)
        return Response(serializer.data)


class ParticipanteActividadViewSet(viewsets.ModelViewSet):
    """
    API para gestionar Participantes en Actividades.
    - GET /api/participantes/ - Listar
    - POST /api/participantes/ - Inscribir
    - DELETE /api/participantes/{id}/ - Dar de baja
    """

    queryset = ParticipanteActividad.objects.select_related(
        "actividad_centro", "ciudadano"
    ).prefetch_related("historial")
    serializer_class = ParticipanteActividadSerializer
    permission_classes = [IsInApiCentroFamiliaGroup]

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
        """Inscribir participante a actividad"""
        try:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                logger.info(
                    f"Participante inscrito: {serializer.instance.ciudadano} en {serializer.instance.actividad_centro}"
                )
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                error_msg = format_serializer_errors(serializer)
                logger.warning(f"Error al inscribir participante: {error_msg}")
                return Response(
                    {"error": error_msg}, status=status.HTTP_400_BAD_REQUEST
                )
        except Exception:
            logger.exception("Error al inscribir participante")
            return Response(
                {"error": "Ocurrió un error interno. Por favor, inténtelo de nuevo más tarde."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["post"])
    def cambiar_estado(self, request, pk=None):
        """Cambiar estado de participante (inscrito/lista_espera/dado_baja)"""
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


class BeneficiarioViewSet(viewsets.ModelViewSet):
    """
    API para gestionar Beneficiarios.
    - GET /api/beneficiarios/ - Listar
    - POST /api/beneficiarios/ - Crear
    - GET /api/beneficiarios/{id}/ - Detalle
    """

    queryset = Beneficiario.objects.select_related(
        "responsable", "provincia", "municipio", "localidad"
    ).prefetch_related("actividades_detalle")
    serializer_class = BeneficiarioSerializer
    permission_classes = [IsInApiCentroFamiliaGroup]

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
        """Listar beneficiarios de un responsable"""
        responsable_id = request.query_params.get("responsable_id")
        if not responsable_id:
            return Response(
                {"error": "responsable_id es requerido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        beneficiarios = self.get_queryset().filter(responsable_id=responsable_id)
        serializer = self.get_serializer(beneficiarios, many=True)
        return Response(serializer.data)


class ResponsableViewSet(viewsets.ModelViewSet):
    """
    API para gestionar Responsables.
    - GET /api/responsables/ - Listar
    - POST /api/responsables/ - Crear
    - GET /api/responsables/{id}/ - Detalle
    """

    queryset = Responsable.objects.select_related("provincia", "municipio", "localidad")
    serializer_class = ResponsableSerializer
    permission_classes = [IsInApiCentroFamiliaGroup]

    def get_queryset(self):
        queryset = super().get_queryset()
        dni = self.request.query_params.get("dni")
        cuil = self.request.query_params.get("cuil")

        if dni:
            queryset = queryset.filter(dni=dni)
        if cuil:
            queryset = queryset.filter(cuil=cuil)

        return queryset


class BeneficiarioResponsableViewSet(viewsets.ModelViewSet):
    """API para gestionar vínculos Beneficiario-Responsable"""

    queryset = BeneficiarioResponsable.objects.select_related(
        "beneficiario", "responsable"
    )
    serializer_class = BeneficiarioResponsableSerializer
    permission_classes = [IsInApiCentroFamiliaGroup]


class InformeCabalRegistroViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API para consultar Registros de Informe CABAL.
    - GET /api/cabal-registros/ - Listar
    - GET /api/cabal-registros/{id}/ - Detalle
    """

    queryset = InformeCabalRegistro.objects.select_related("archivo", "centro")
    serializer_class = InformeCabalRegistroSerializer
    permission_classes = [IsInApiCentroFamiliaGroup]

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
        """Listar registros CABAL de un centro"""
        centro_id = request.query_params.get("centro_id")
        if not centro_id:
            return Response(
                {"error": "centro_id es requerido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        registros = self.get_queryset().filter(centro_id=centro_id)
        serializer = self.get_serializer(registros, many=True)
        return Response(serializer.data)


class CabalArchivoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API para consultar Archivos CABAL.
    - GET /api/cabal-archivos/ - Listar
    - GET /api/cabal-archivos/{id}/ - Detalle con registros
    """

    queryset = CabalArchivo.objects.select_related("usuario").prefetch_related(
        "registros"
    )
    serializer_class = CabalArchivoSerializer
    permission_classes = [IsInApiCentroFamiliaGroup]
