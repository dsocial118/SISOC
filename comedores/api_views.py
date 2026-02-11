from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.response import Response

from comedores.api_serializers import ComedorDetailSerializer
from comedores.models import (
    AuditComedorPrograma,
    Comedor,
    ImagenComedor,
    Observacion,
)
from core.api_auth import HasAPIKey
from relevamientos.models import ClasificacionComedor, Relevamiento
from rendicioncuentasmensual.models import RendicionCuentaMensual
from django.db.models import Prefetch


@extend_schema(tags=["Comedores"])
class ComedorDetailViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = ComedorDetailSerializer
    permission_classes = [HasAPIKey]
    http_method_names = ["get", "head", "options"]

    def list(self, request, *args, **kwargs):
        return Response(
            {"detail": "Listado no disponible en este endpoint."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def get_queryset(self):
        return (
            Comedor.objects.select_related(
                "provincia",
                "municipio",
                "localidad",
                "referente",
                "organizacion",
                "programa",
                "tipocomedor",
                "dupla",
                "ultimo_estado__estado_general__estado_actividad",
                "ultimo_estado__estado_general__estado_proceso",
                "ultimo_estado__estado_general__estado_detalle",
            )
            .prefetch_related(
                "dupla__tecnico",
                Prefetch(
                    "imagenes",
                    queryset=ImagenComedor.objects.only("id", "imagen"),
                    to_attr="imagenes_optimized",
                ),
                Prefetch(
                    "relevamiento_set",
                    queryset=Relevamiento.objects.only(
                        "id",
                        "fecha_visita",
                        "estado",
                        "prestacion",
                    ).order_by("-fecha_visita", "-id"),
                    to_attr="relevamientos_optimized",
                ),
                Prefetch(
                    "observacion_set",
                    queryset=Observacion.objects.only(
                        "id",
                        "observador",
                        "fecha_visita",
                        "observacion",
                    ).order_by("-fecha_visita")[:3],
                    to_attr="observaciones_optimized",
                ),
                Prefetch(
                    "clasificacioncomedor_set",
                    queryset=ClasificacionComedor.objects.select_related(
                        "categoria"
                    ).only(
                        "id",
                        "puntuacion_total",
                        "fecha",
                        "categoria__nombre",
                        "relevamiento",
                    ).order_by("-fecha")[:3],
                    to_attr="clasificaciones_optimized",
                ),
                Prefetch(
                    "rendiciones_cuentas_mensuales",
                    queryset=RendicionCuentaMensual.objects.only(
                        "id",
                        "mes",
                        "anio",
                        "observaciones",
                        "documento_adjunto",
                        "ultima_modificacion",
                        "fecha_creacion",
                    ).order_by("-anio", "-mes"),
                    to_attr="rendiciones_optimized",
                ),
                Prefetch(
                    "programa_changes",
                    queryset=AuditComedorPrograma.objects.select_related(
                        "from_programa",
                        "to_programa",
                        "changed_by",
                    )
                    .only(
                        "id",
                        "from_programa__nombre",
                        "to_programa__nombre",
                        "changed_at",
                        "changed_by__username",
                        "changed_by__first_name",
                        "changed_by__last_name",
                    )
                    .order_by("-changed_at", "-id"),
                    to_attr="programa_changes_optimized",
                ),
            )
            .order_by("-id")
        )
