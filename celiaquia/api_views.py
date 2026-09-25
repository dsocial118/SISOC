"""API REST de Celiaquia.

Dos reglas que ordenan todo este modulo:

1. **El alcance se aplica en `get_queryset()`**, siempre, reusando
   `celiaquia.scope`. Las pantallas filtraban por rol y territorio; un endpoint
   que devuelva el queryset pelado expone expedientes de otras provincias.
2. **Las escrituras delegan en `celiaquia/services/`.** Los expedientes tienen
   maquina de estados, historial y cupos: persistir desde el serializer saltea
   todo eso. Por eso los ViewSets son de lectura y las transiciones son
   `@action` que llaman al service.
"""

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Count
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from celiaquia.api_serializers import (
    AccionResultadoSerializer,
    AsignacionTecnicoSerializer,
    AsignarTecnicoSerializer,
    CupoMovimientoSerializer,
    DocumentoLegajoSerializer,
    EstadoExpedienteSerializer,
    EstadoLegajoSerializer,
    ExpedienteEstadoHistorialSerializer,
    ExpedienteSerializer,
    LegajoSerializer,
    OrganismoSerializer,
    PagoExpedienteSerializer,
    PagoNominaSerializer,
    ProvinciaCupoSerializer,
    SolicitarSubsanacionSerializer,
    SubsanacionSerializer,
    TipoCruceSerializer,
    TipoDocumentoSerializer,
)
from celiaquia.models import (
    CupoMovimiento,
    EstadoExpediente,
    EstadoLegajo,
    Expediente,
    ExpedienteCiudadano,
    Organismo,
    PagoExpediente,
    PagoNomina,
    ProvinciaCupo,
    Subsanacion,
    TipoCruce,
    TipoDocumento,
)
from celiaquia.scope import (
    is_admin,
    is_coordinador,
    is_provincial,
    scope_expedientes,
)
from celiaquia.services.asignacion_service import AsignacionService
from celiaquia.services.cupo_service import CupoService
from celiaquia.services.documentos_service import DocumentosService
from celiaquia.services.expediente_service import ExpedienteService
from celiaquia.services.legajo_service import LegajoService
from users.models import User


def _traducir_error(exc: Exception) -> ValidationError:
    """Los services levantan ValidationError de Django; la API responde 400."""

    mensajes = getattr(exc, "messages", None) or [str(exc)]
    return ValidationError({"detail": mensajes})


class CeliaquiaCatalogoViewSet(viewsets.ReadOnlyModelViewSet):
    """Catalogos: los lee cualquier usuario autenticado del modulo."""

    pagination_class = None


class EstadoExpedienteViewSet(CeliaquiaCatalogoViewSet):
    queryset = EstadoExpediente.objects.all().order_by("nombre")
    serializer_class = EstadoExpedienteSerializer


class EstadoLegajoViewSet(CeliaquiaCatalogoViewSet):
    queryset = EstadoLegajo.objects.all().order_by("nombre")
    serializer_class = EstadoLegajoSerializer


class OrganismoViewSet(CeliaquiaCatalogoViewSet):
    queryset = Organismo.objects.all().order_by("nombre")
    serializer_class = OrganismoSerializer


class TipoCruceViewSet(CeliaquiaCatalogoViewSet):
    queryset = TipoCruce.objects.all().order_by("nombre")
    serializer_class = TipoCruceSerializer


class TipoDocumentoViewSet(CeliaquiaCatalogoViewSet):
    serializer_class = TipoDocumentoSerializer
    queryset = TipoDocumento.objects.none()

    def get_queryset(self):
        return DocumentosService.obtener_tipos_documento_activos()


class ExpedienteViewSet(viewsets.ReadOnlyModelViewSet):
    """Expedientes visibles para el usuario, con sus transiciones de estado."""

    serializer_class = ExpedienteSerializer
    # Solo para que el schema derive el tipo del pk: get_queryset() manda.
    queryset = Expediente.objects.none()

    def get_queryset(self):
        queryset = (
            Expediente.objects.select_related(
                "estado", "usuario_provincia__profile__provincia"
            )
            .annotate(legajos_total_count=Count("expediente_ciudadanos", distinct=True))
            .order_by("-fecha_creacion", "pk")
        )
        queryset = scope_expedientes(queryset, self.request.user)

        estado = (self.request.query_params.get("estado") or "").strip()
        if estado:
            queryset = queryset.filter(estado__nombre__iexact=estado)
        numero = (self.request.query_params.get("numero_expediente") or "").strip()
        if numero:
            queryset = queryset.filter(numero_expediente__icontains=numero)
        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter("estado", str, description="Nombre exacto del estado."),
            OpenApiParameter(
                "numero_expediente", str, description="Coincidencia parcial."
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    # --- Sub-recursos ------------------------------------------------------

    @extend_schema(responses=LegajoSerializer(many=True))
    @action(detail=True, methods=["get"])
    def legajos(self, request, pk=None):
        """Legajos del expediente (`ExpedienteCiudadano`)."""

        expediente = self.get_object()
        queryset = LegajoService.listar_legajos(expediente)
        pagina = self.paginate_queryset(queryset)
        serializer = LegajoSerializer(
            pagina if pagina is not None else queryset,
            many=True,
            context=self.get_serializer_context(),
        )
        if pagina is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @extend_schema(responses=ExpedienteEstadoHistorialSerializer(many=True))
    @action(detail=True, methods=["get"], url_path="historial-estados")
    def historial_estados(self, request, pk=None):
        expediente = self.get_object()
        queryset = expediente.historial.select_related(
            "estado_nuevo", "estado_anterior", "usuario"
        ).order_by("-fecha")
        return Response(
            ExpedienteEstadoHistorialSerializer(
                queryset, many=True, context=self.get_serializer_context()
            ).data
        )

    @extend_schema(responses=AsignacionTecnicoSerializer(many=True))
    @action(detail=True, methods=["get"])
    def asignaciones(self, request, pk=None):
        expediente = self.get_object()
        queryset = AsignacionService.obtener_historial_asignaciones(expediente)
        return Response(
            AsignacionTecnicoSerializer(
                queryset, many=True, context=self.get_serializer_context()
            ).data
        )

    @extend_schema(responses=LegajoSerializer(many=True))
    @action(detail=True, methods=["get"], url_path="fuera-de-cupo")
    def fuera_de_cupo(self, request, pk=None):
        expediente = self.get_object()
        queryset = CupoService.lista_fuera_de_cupo_por_expediente(expediente.pk)
        return Response(
            LegajoSerializer(
                queryset, many=True, context=self.get_serializer_context()
            ).data
        )

    # --- Transiciones (delegan en el service) ------------------------------

    def _exigir_gestion(self):
        """Procesar/confirmar son operaciones de la provincia duena, o admin."""

        user = self.request.user
        if not (is_admin(user) or is_provincial(user) or is_coordinador(user)):
            raise PermissionDenied("No tiene permisos para operar el expediente.")

    @extend_schema(request=None, responses=AccionResultadoSerializer)
    @action(detail=True, methods=["post"])
    def procesar(self, request, pk=None):
        """Procesa el Excel masivo y crea los legajos."""

        self._exigir_gestion()
        expediente = self.get_object()
        try:
            ExpedienteService.procesar_expediente(expediente, request.user)
        except DjangoValidationError as exc:
            raise _traducir_error(exc) from exc
        expediente.refresh_from_db()
        return Response(
            {
                "detail": "Expediente procesado.",
                "expediente": ExpedienteSerializer(
                    expediente, context=self.get_serializer_context()
                ).data,
            }
        )

    @extend_schema(request=None, responses=AccionResultadoSerializer)
    @action(detail=True, methods=["post"], url_path="confirmar-envio")
    def confirmar_envio(self, request, pk=None):
        """Cierra la carga provincial y envia el expediente a revision."""

        self._exigir_gestion()
        expediente = self.get_object()
        try:
            ExpedienteService.confirmar_envio(expediente, request.user)
        except DjangoValidationError as exc:
            raise _traducir_error(exc) from exc
        expediente.refresh_from_db()
        return Response(
            {
                "detail": "Envio confirmado.",
                "expediente": ExpedienteSerializer(
                    expediente, context=self.get_serializer_context()
                ).data,
            }
        )

    @extend_schema(
        request=AsignarTecnicoSerializer, responses=AccionResultadoSerializer
    )
    @action(detail=True, methods=["post"], url_path="asignar-tecnico")
    def asignar_tecnico(self, request, pk=None):
        if not (is_admin(request.user) or is_coordinador(request.user)):
            raise PermissionDenied("Solo coordinacion puede asignar tecnicos.")
        expediente = self.get_object()
        entrada = AsignarTecnicoSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        tecnico = get_object_or_404(User, pk=entrada.validated_data["tecnico_id"])
        try:
            ExpedienteService.asignar_tecnico(expediente, tecnico, request.user)
        except DjangoValidationError as exc:
            raise _traducir_error(exc) from exc
        return Response({"detail": "Tecnico asignado."})

    @extend_schema(request=None, responses=AccionResultadoSerializer)
    @action(detail=True, methods=["post"], url_path="desasignar-tecnico")
    def desasignar_tecnico(self, request, pk=None):
        if not (is_admin(request.user) or is_coordinador(request.user)):
            raise PermissionDenied("Solo coordinacion puede desasignar tecnicos.")
        expediente = self.get_object()
        try:
            AsignacionService.desasignar_tecnico(expediente, request.user)
        except DjangoValidationError as exc:
            raise _traducir_error(exc) from exc
        return Response({"detail": "Tecnico desasignado."})


class LegajoViewSet(viewsets.ReadOnlyModelViewSet):
    """Legajos, acotados a los expedientes que el usuario puede ver."""

    serializer_class = LegajoSerializer
    # Solo para que el schema derive el tipo del pk: get_queryset() manda.
    queryset = ExpedienteCiudadano.objects.none()

    def get_queryset(self):
        expedientes_visibles = scope_expedientes(
            Expediente.objects.all(), self.request.user
        )
        queryset = (
            ExpedienteCiudadano.objects.filter(expediente__in=expedientes_visibles)
            .select_related("estado", "ciudadano", "expediente")
            .order_by("-creado_en", "pk")
        )

        expediente_id = (self.request.query_params.get("expediente") or "").strip()
        if expediente_id.isdigit():
            queryset = queryset.filter(expediente_id=int(expediente_id))
        revision = (self.request.query_params.get("revision_tecnico") or "").strip()
        if revision:
            queryset = queryset.filter(revision_tecnico=revision.upper())
        estado_cupo = (self.request.query_params.get("estado_cupo") or "").strip()
        if estado_cupo:
            queryset = queryset.filter(estado_cupo=estado_cupo.upper())
        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter("expediente", int),
            OpenApiParameter("revision_tecnico", str),
            OpenApiParameter("estado_cupo", str),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(responses=DocumentoLegajoSerializer(many=True))
    @action(detail=True, methods=["get"])
    def documentos(self, request, pk=None):
        legajo = self.get_object()
        queryset = DocumentosService.obtener_documentos_legajo(legajo)
        return Response(
            DocumentoLegajoSerializer(
                queryset, many=True, context=self.get_serializer_context()
            ).data
        )

    @extend_schema(responses=SubsanacionSerializer(many=True))
    @action(detail=True, methods=["get"])
    def subsanaciones(self, request, pk=None):
        legajo = self.get_object()
        queryset = Subsanacion.objects.filter(legajo=legajo).select_related(
            "solicitada_por", "respondida_por"
        )
        return Response(
            SubsanacionSerializer(
                queryset.order_by("-solicitada_en"),
                many=True,
                context=self.get_serializer_context(),
            ).data
        )

    @extend_schema(
        request=SolicitarSubsanacionSerializer, responses=AccionResultadoSerializer
    )
    @action(detail=True, methods=["post"], url_path="solicitar-subsanacion")
    def solicitar_subsanacion(self, request, pk=None):
        """Marca el legajo para subsanar. Es una accion del tecnico revisor."""

        legajo = self.get_object()
        entrada = SolicitarSubsanacionSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        try:
            LegajoService.solicitar_subsanacion(
                legajo, entrada.validated_data["motivo"], request.user
            )
        except DjangoValidationError as exc:
            raise _traducir_error(exc) from exc
        return Response({"detail": "Subsanacion solicitada."})


class ProvinciaCupoViewSet(viewsets.ReadOnlyModelViewSet):
    """Cupos por provincia. Solo lectura: el alta la hace `CupoService`."""

    serializer_class = ProvinciaCupoSerializer
    queryset = ProvinciaCupo.objects.none()

    def get_queryset(self):
        return ProvinciaCupo.objects.select_related("provincia").order_by(
            "provincia__nombre"
        )

    @extend_schema(responses=ProvinciaCupoSerializer)
    @action(detail=True, methods=["get"])
    def metricas(self, request, pk=None):
        """Metricas calculadas por `CupoService`, no el contador crudo."""

        cupo = self.get_object()
        return Response(CupoService.metrics_por_provincia(cupo.provincia))

    @extend_schema(responses=LegajoSerializer(many=True))
    @action(detail=True, methods=["get"])
    def ocupados(self, request, pk=None):
        cupo = self.get_object()
        queryset = CupoService.lista_ocupados_por_provincia(cupo.provincia)
        return Response(
            LegajoSerializer(
                queryset, many=True, context=self.get_serializer_context()
            ).data
        )

    @extend_schema(responses=LegajoSerializer(many=True))
    @action(detail=True, methods=["get"])
    def suspendidos(self, request, pk=None):
        cupo = self.get_object()
        queryset = CupoService.lista_suspendidos_por_provincia(cupo.provincia)
        return Response(
            LegajoSerializer(
                queryset, many=True, context=self.get_serializer_context()
            ).data
        )


class CupoMovimientoViewSet(viewsets.ReadOnlyModelViewSet):
    """Auditoria de movimientos de cupo."""

    serializer_class = CupoMovimientoSerializer
    queryset = CupoMovimiento.objects.none()

    def get_queryset(self):
        queryset = CupoMovimiento.objects.select_related(
            "provincia", "usuario"
        ).order_by("-creado_en", "pk")
        provincia_id = (self.request.query_params.get("provincia") or "").strip()
        if provincia_id.isdigit():
            queryset = queryset.filter(provincia_id=int(provincia_id))
        expediente_id = (self.request.query_params.get("expediente") or "").strip()
        if expediente_id.isdigit():
            queryset = queryset.filter(expediente_id=int(expediente_id))
        return queryset


class PagoExpedienteViewSet(viewsets.ReadOnlyModelViewSet):
    """Lotes de pago y su nomina."""

    serializer_class = PagoExpedienteSerializer
    queryset = PagoExpediente.objects.none()

    def get_queryset(self):
        queryset = PagoExpediente.objects.select_related("provincia").order_by(
            "-creado_en", "pk"
        )
        periodo = (self.request.query_params.get("periodo") or "").strip()
        if periodo:
            queryset = queryset.filter(periodo=periodo)
        estado = (self.request.query_params.get("estado") or "").strip()
        if estado:
            queryset = queryset.filter(estado=estado)
        return queryset

    @extend_schema(responses=PagoNominaSerializer(many=True))
    @action(detail=True, methods=["get"])
    def nomina(self, request, pk=None):
        pago = self.get_object()
        queryset = PagoNomina.objects.filter(pago=pago).order_by("apellido", "nombre")
        pagina = self.paginate_queryset(queryset)
        serializer = PagoNominaSerializer(
            pagina if pagina is not None else queryset,
            many=True,
            context=self.get_serializer_context(),
        )
        if pagina is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)
