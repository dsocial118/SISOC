import logging

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

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
    ProvinciaSerializer,
    MunicipioSerializer,
    LocalidadSerializer,
)
from core.api_auth import HasAPIKey
from core.models import Provincia, Municipio, Localidad
from core.soft_delete_views import is_soft_deletable_instance
from core.utils import format_serializer_errors

logger = logging.getLogger("django")


class SoftDeleteDestroyMixin:
    """Use logical delete for soft-delete capable models."""

    def perform_destroy(self, instance):
        if is_soft_deletable_instance(instance):
            user = self.request.user if getattr(self.request.user, "is_authenticated", False) else None
            instance.delete(user=user, cascade=True)
            return
        super().perform_destroy(instance)


@extend_schema(tags=["Centros"])
class CentroViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    """
    API para gestionar Centros de Familia.

    Información que devuelve:
    - Datos básicos del centro (nombre, código, tipo)
    - Información de contacto (teléfono, celular, correo)
    - Ubicación geográfica (provincia, municipio, localidad)
    - Referente asignado
    - Categorías de actividades disponibles en el centro

    Filtros disponibles:
    - activo: true/false
    - provincia_id: ID de provincia
    - municipio_id: ID de municipio
    - localidad_id: ID de localidad
    - categoria_id: ID de categoría de actividad
    """

    queryset = Centro.objects.select_related(
        "referente", "provincia", "municipio", "localidad"
    )
    serializer_class = CentroSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtro por estado activo
        activo = self.request.query_params.get("activo")
        if activo is not None:
            queryset = queryset.filter(activo=activo.lower() == "true")

        # Filtros de ubicación
        provincia_id = self.request.query_params.get("provincia_id")
        municipio_id = self.request.query_params.get("municipio_id")
        localidad_id = self.request.query_params.get("localidad_id")

        if provincia_id:
            queryset = queryset.filter(provincia_id=provincia_id)
        if municipio_id:
            queryset = queryset.filter(municipio_id=municipio_id)
        if localidad_id:
            queryset = queryset.filter(localidad_id=localidad_id)

        # Filtro por categoría de actividad
        categoria_id = self.request.query_params.get("categoria_id")
        if categoria_id:
            queryset = queryset.filter(
                actividadcentro__actividad__categoria_id=categoria_id
            ).distinct()

        return queryset

    @action(detail=False, methods=["get"])
    def activos(self, request):
        """Listar solo centros activos con todos los filtros disponibles"""
        centros = self.get_queryset().filter(activo=True)
        serializer = self.get_serializer(centros, many=True)
        return Response(serializer.data)


@extend_schema(tags=["Actividades"])
class ActividadViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    """
    API para gestionar Actividades.

    Información que devuelve:
    - Nombre de la actividad
    - Categoría a la que pertenece
    - ID único de la actividad

    Filtros disponibles:
    - categoria_id: Filtrar actividades por categoría
    """

    queryset = Actividad.objects.select_related("categoria")
    serializer_class = ActividadSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        categoria_id = self.request.query_params.get("categoria_id")
        if categoria_id:
            queryset = queryset.filter(categoria_id=categoria_id)
        return queryset


@extend_schema(tags=["Categorías"])
class CategoriaViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    """
    API para gestionar Categorías de Actividades.

    Información que devuelve:
    - ID de la categoría
    - Nombre de la categoría (ej: Deportiva, Cultural, Educativa)
    """

    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [HasAPIKey]


@extend_schema(tags=["Actividades por Centro"])
class ActividadCentroViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    """
    API para gestionar Actividades por Centro.

    Información que devuelve:
    - Actividad específica de un centro
    - Horarios (desde/hasta)
    - Días de la semana
    - Cantidad estimada de participantes
    - Estado (planificada, en_curso, finalizada)
    - Precio de la actividad
    - Información del centro y actividad asociada

    Filtros disponibles:
    - centro_id: Actividades de un centro específico
    - estado: Estado de la actividad
    """

    queryset = ActividadCentro.objects.select_related(
        "centro", "actividad", "actividad__categoria"
    ).prefetch_related("dias", "sexoact")
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

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="centro_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=True,
                description="ID del centro para filtrar actividades",
            ),
            OpenApiParameter(
                name="estado",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Estado de la actividad (planificada, en_curso, finalizada)",
            ),
        ],
        description="Listar actividades de un centro específico",
    )
    @action(detail=False, methods=["get"])
    def por_centro(self, request):
        """Listar actividades de un centro específico"""
        centro_id = request.query_params.get("centro_id")
        if not centro_id:
            return Response(
                {"error": "centro_id es requerido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Usar queryset base sin filtros aplicados y filtrar directamente
        actividades = self.queryset.filter(centro_id=centro_id)

        # Aplicar filtros adicionales si existen
        estado = request.query_params.get("estado")
        if estado:
            actividades = actividades.filter(estado=estado)

        serializer = self.get_serializer(actividades, many=True)
        return Response(serializer.data)


@extend_schema(tags=["Participantes"])
class ParticipanteActividadViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    """
    API para gestionar Participantes en Actividades.

    Información que devuelve:
    - Datos del ciudadano participante
    - Actividad en la que está inscrito
    - Estado de inscripción (inscrito, lista_espera, dado_baja)
    - Fechas de registro y modificación
    - Historial de cambios de estado

    Filtros disponibles:
    - actividad_centro_id: Participantes de una actividad específica
    - estado: Estado de inscripción
    """

    queryset = ParticipanteActividad.objects.select_related(
        "actividad_centro", "ciudadano"
    ).prefetch_related("historial")
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
                {
                    "error": "Ocurrió un error interno. Por favor, inténtelo de nuevo más tarde."
                },
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


@extend_schema(tags=["Beneficiarios"])
class BeneficiarioViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    """
    API para gestionar Beneficiarios.

    Información que devuelve:
    - Datos personales (nombre, apellido, DNI, CUIL, género)
    - Fecha de nacimiento
    - Domicilio completo (provincia, municipio, localidad, dirección)
    - Información académica (nivel educativo actual y máximo)
    - Actividades preferidas y extracurriculares
    - Datos del responsable asociado
    - Información de contacto

    Filtros disponibles:
    - responsable_id: Beneficiarios de un responsable específico
    - dni: Búsqueda por DNI
    """

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

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="responsable_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=True,
                description="ID del responsable para filtrar beneficiarios",
            ),
        ],
        description="Listar beneficiarios de un responsable específico",
    )
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


@extend_schema(tags=["Responsables"])
class ResponsableViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    """
    API para gestionar Responsables.

    Información que devuelve:
    - Datos personales (nombre, apellido, DNI, CUIL, género)
    - Fecha de nacimiento
    - Vínculo parental (Padre/Madre, Tutor/Tutora)
    - Domicilio completo (provincia, municipio, localidad, dirección)
    - Información de contacto (celular, teléfono fijo, correo)
    - Fechas de creación y modificación

    Filtros disponibles:
    - dni: Búsqueda por DNI
    - cuil: Búsqueda por CUIL
    """

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


@extend_schema(tags=["Vínculos"])
class BeneficiarioResponsableViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    """
    API para gestionar vínculos Beneficiario-Responsable.

    Información que devuelve:
    - Relación entre beneficiario y responsable
    - Tipo de vínculo parental
    - Nombres completos de ambas partes
    - Fechas de creación y modificación del vínculo
    """

    queryset = BeneficiarioResponsable.objects.select_related(
        "beneficiario", "responsable"
    )
    serializer_class = BeneficiarioResponsableSerializer
    permission_classes = [HasAPIKey]


@extend_schema(tags=["Informes CABAL"])
class InformeCabalRegistroViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API para consultar Registros de Informe CABAL.

    Información que devuelve:
    - Datos de transacciones CABAL por centro
    - Número de tarjeta y autorización
    - Importe y fecha de transacción
    - Razón social del comercio
    - Estado de coincidencia con centros
    - Número de fila del archivo original

    Filtros disponibles:
    - archivo_id: Registros de un archivo específico
    - centro_id: Registros de un centro específico
    - no_coincidente: Registros sin centro asociado
    """

    queryset = InformeCabalRegistro.objects.select_related("archivo", "centro")
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

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="centro_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=True,
                description="ID del centro para filtrar registros CABAL",
            ),
        ],
        description="Listar registros CABAL de un centro específico",
    )
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


@extend_schema(tags=["Archivos CABAL"])
class CabalArchivoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API para consultar Archivos CABAL.

    Información que devuelve:
    - Información del archivo subido (nombre original, fecha)
    - Usuario que subió el archivo
    - Estadísticas de procesamiento (total filas, válidas, inválidas)
    - Todos los registros contenidos en el archivo
    - Advertencias sobre nombres duplicados
    """

    queryset = CabalArchivo.objects.select_related("usuario").prefetch_related(
        "registros"
    )
    serializer_class = CabalArchivoSerializer
    permission_classes = [HasAPIKey]


# ViewSets de Ubicación
@extend_schema(tags=["Ubicación"])
class ProvinciaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API para consultar Provincias.

    Información que devuelve:
    - Lista completa de provincias de Argentina
    - ID único y nombre de cada provincia
    - Ordenadas alfabéticamente
    """

    queryset = Provincia.objects.all().order_by("nombre")
    serializer_class = ProvinciaSerializer
    permission_classes = [HasAPIKey]


@extend_schema(tags=["Ubicación"])
class MunicipioViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API para consultar Municipios.

    Información que devuelve:
    - Lista de municipios con su provincia asociada
    - ID único, nombre del municipio y nombre de la provincia
    - Ordenados alfabéticamente

    Filtros disponibles:
    - provincia_id: Municipios de una provincia específica
    """

    queryset = Municipio.objects.select_related("provincia").order_by("nombre")
    serializer_class = MunicipioSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        provincia_id = self.request.query_params.get("provincia_id")
        if provincia_id:
            queryset = queryset.filter(provincia_id=provincia_id)
        return queryset


@extend_schema(tags=["Ubicación"])
class LocalidadViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API para consultar Localidades.

    Información que devuelve:
    - Lista de localidades con municipio y provincia asociados
    - ID único, nombre de localidad, municipio y provincia
    - Ordenadas alfabéticamente

    Filtros disponibles:
    - municipio_id: Localidades de un municipio específico
    - provincia_id: Localidades de una provincia específica
    """

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
