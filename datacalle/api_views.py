"""API que consume la app DataCalle (contrato D2.5).

El alcance lo resuelve el servidor: la app no manda filtros de usuario ni de
provincia. Un entrevistador sólo ve los relevamientos donde está en el equipo.
"""

import logging

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.response import Response

from datacalle.api_permissions import EsRelevadorCalle
from datacalle.api_serializers import (
    CierreRelevamientoSerializer,
    EncuestaSerializer,
    EncuestaUpsertSerializer,
    RelevamientoTareaSerializer,
)
from datacalle.models import Relevamiento
from datacalle.services import (
    RelevamientoCerrado,
    get_catalogos,
    get_cuestionario,
    get_version,
    cerrar_relevamiento,
    get_encuestas_queryset,
    get_relevamientos_queryset,
    upsert_encuesta,
)

logger = logging.getLogger("django")

ERROR_CERRADO = {
    "detail": "El relevamiento está finalizado y no acepta más casos.",
    "codigo": "relevamiento_cerrado",
}


def mis_relevamientos(user):
    """Relevamientos donde el usuario está en el equipo (D2.2)."""
    return get_relevamientos_queryset().filter(equipo=user).distinct()


@extend_schema(tags=["DataCalle"])
class RelevamientoViewSet(viewsets.ReadOnlyModelViewSet):
    """Mis tareas: sólo lectura, más el cierre en campo."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [EsRelevadorCalle]
    serializer_class = RelevamientoTareaSerializer

    def get_queryset(self):
        queryset = mis_relevamientos(self.request.user)
        estado = (self.request.query_params.get("estado") or "").strip()
        if estado in Relevamiento.Estado.values:
            queryset = queryset.filter(estado=estado)
        desde = (self.request.query_params.get("desde") or "").strip()
        if desde:
            queryset = queryset.filter(updated_at__gte=desde)
        return queryset.order_by("-updated_at")

    @extend_schema(request=None, responses=EncuestaSerializer)
    @action(detail=True, methods=["get"], url_path="encuestas")
    def encuestas(self, request, pk=None):
        """Casos ya sincronizados: sirve para recuperar un dispositivo."""
        relevamiento = self.get_object()
        queryset = get_encuestas_queryset(relevamiento).order_by("-updated_at")
        pagina = self.paginate_queryset(queryset)
        serializer = EncuestaSerializer(pagina or queryset, many=True)
        if pagina is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @extend_schema(request=CierreRelevamientoSerializer)
    @action(detail=True, methods=["post"], url_path="cerrar")
    def cerrar(self, request, pk=None):
        """Cierre desde la app. Idempotente: cerrar dos veces no es error."""
        relevamiento = self.get_object()
        serializer = CierreRelevamientoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        relevamiento, cerrado_ahora = cerrar_relevamiento(
            relevamiento=relevamiento,
            user=request.user,
            datos=serializer.validated_data,
        )
        if not cerrado_ahora:
            logger.info(
                "Cierre repetido de relevamiento %s por user_id=%s",
                relevamiento.pk,
                request.user.id,
            )
        return Response(
            RelevamientoTareaSerializer(relevamiento).data,
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=["DataCalle"])
class EncuestaViewSet(viewsets.GenericViewSet):
    """Escritura de casos: upsert idempotente por UUID del dispositivo."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [EsRelevadorCalle]
    serializer_class = EncuestaSerializer

    def get_queryset(self):
        return get_encuestas_queryset().filter(
            relevamiento__in=mis_relevamientos(self.request.user)
        )

    def retrieve(self, request, pk=None):
        encuesta = get_object_or_404(self.get_queryset(), pk=pk)
        return Response(EncuestaSerializer(encuesta).data)

    @extend_schema(request=EncuestaUpsertSerializer, responses=EncuestaSerializer)
    def update(self, request, pk=None):
        serializer = EncuestaUpsertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = dict(serializer.validated_data)

        relevamiento = get_object_or_404(
            mis_relevamientos(request.user), pk=datos.pop("relevamiento_id")
        )
        try:
            encuesta, creada = upsert_encuesta(
                encuesta_id=pk,
                relevamiento=relevamiento,
                datos=datos,
                user=request.user,
            )
        except RelevamientoCerrado:
            return Response(ERROR_CERRADO, status=status.HTTP_409_CONFLICT)

        return Response(
            EncuestaSerializer(encuesta).data,
            status=status.HTTP_201_CREATED if creada else status.HTTP_200_OK,
        )

    def destroy(self, request, pk=None):
        encuesta = get_object_or_404(self.get_queryset(), pk=pk)
        encuesta.delete(user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["DataCalle"])
class CatalogoViewSet(viewsets.ViewSet):
    """Catálogos y cuestionario vigentes (N9).

    Permite corregir textos y opciones sin publicar una versión de la app: ella
    cachea la respuesta y usa su copia embebida como respaldo.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [EsRelevadorCalle]

    @extend_schema(responses=None)
    def list(self, request):
        return Response(
            {
                "version": get_version(),
                "catalogos": get_catalogos(),
                "cuestionario": get_cuestionario(),
            }
        )
