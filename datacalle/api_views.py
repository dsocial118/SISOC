"""API que consume la app DataCalle (contrato D2.5).

El alcance lo resuelve el servidor: la app no manda filtros de usuario ni de
provincia. El entrevistador sólo ve los relevamientos donde está en el
equipo; el coordinador y el administrador ven más (ver ``mis_relevamientos``).
"""

import logging

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.response import Response

from datacalle.api_permissions import TieneAccesoDataCalle
from datacalle.api_serializers import (
    CierreRelevamientoSerializer,
    EncuestaSerializer,
    EncuestaUpsertSerializer,
    RelevamientoTareaSerializer,
)
from datacalle.models import Relevamiento
from datacalle.services import (
    RelevamientoCerrado,
    RelevamientoNoIniciado,
    get_catalogos,
    get_cuestionario,
    get_version,
    cerrar_relevamiento,
    get_encuestas_queryset,
    get_relevamientos_queryset,
    upsert_encuesta,
)
from users.services_datacalle import (
    es_coordinador_datacalle,
    get_datacalle_provincia_ids,
)

logger = logging.getLogger("django")

# Los dos rechazos son 409, pero no significan lo mismo para la app: cerrado es
# definitivo y el caso no se va a poder subir nunca; no iniciado se resuelve
# solo cuando arranca el operativo. ``reintentable`` lo hace explícito para que
# la cola offline no descarte una jornada de campo por confundirlos. Es aditivo:
# los clientes que no lo lean siguen funcionando igual.
ERROR_CERRADO = {
    "detail": "El relevamiento está finalizado y no acepta más casos.",
    "codigo": "relevamiento_cerrado",
    "reintentable": False,
}
ERROR_NO_INICIADO = {
    "detail": "El relevamiento todavía no empezó.",
    "codigo": "relevamiento_no_iniciado",
    "reintentable": True,
}
# QA-0020: el cierre alcanza a todo el equipo, así que no es del relevador en
# campo sino del coordinador desde el backoffice. No es reintentable: la app
# no destraba esto esperando, tiene que dejar de ofrecer la acción.
ERROR_CIERRE_NO_AUTORIZADO = {
    "detail": "Sólo el coordinador cierra el relevamiento, desde SISOC.",
    "codigo": "cierre_no_autorizado",
    "reintentable": False,
}


def mis_relevamientos(user):
    """Operativos que el usuario ve en la app, segun su rol (D2.2).

    La jerarquia es decreciente: el entrevistador ve los suyos, el coordinador
    todos los de su provincia —asi puede relevar sin estar en el equipo— y el
    administrador todos.
    """
    queryset = get_relevamientos_queryset()
    if not es_coordinador_datacalle(user):
        return queryset.filter(equipo=user).distinct()

    provincia_ids = get_datacalle_provincia_ids(user)
    if provincia_ids is None:
        return queryset.distinct()
    if not provincia_ids:
        return queryset.none()
    return queryset.filter(provincia_id__in=provincia_ids).distinct()


@extend_schema(tags=["DataCalle"])
class RelevamientoViewSet(viewsets.ReadOnlyModelViewSet):
    """Mis tareas: sólo lectura, más el cierre en campo."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [TieneAccesoDataCalle]
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
        """Cierre del operativo. Idempotente: cerrar dos veces no es error.

        QA-0020: queda reservado al coordinador. El relevador comparte el
        operativo con el resto del equipo, así que cerrarlo desde campo le
        corta la jornada a los demás.
        """
        if not es_coordinador_datacalle(request.user):
            logger.warning(
                "Intento de cierre sin rol de coordinador: relevamiento=%s user_id=%s",
                pk,
                request.user.id,
            )
            return Response(
                ERROR_CIERRE_NO_AUTORIZADO, status=status.HTTP_403_FORBIDDEN
            )

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
    permission_classes = [TieneAccesoDataCalle]
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
        except RelevamientoNoIniciado:
            return Response(ERROR_NO_INICIADO, status=status.HTTP_409_CONFLICT)

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
    permission_classes = [TieneAccesoDataCalle]

    @extend_schema(responses=None)
    def list(self, request):
        return Response(
            {
                "version": get_version(),
                "catalogos": get_catalogos(),
                "cuestionario": get_cuestionario(),
            }
        )
