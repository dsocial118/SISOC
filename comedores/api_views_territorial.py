"""API mobile para usuarios territoriales de comedores (SISOC - Mobile).

El territorial (usuario SISOC con ``Profile.es_territorial_comedor=True``) lee
sus comedores asignados con scope por las provincias que tiene cargadas en
``TerritorialComedorProvincia``. Auth por DRF Token.
"""

from django.core.files.storage import default_storage
from django.db import IntegrityError
from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from comedores.api_serializers import ComedorDetailSerializer
from comedores.models import Comedor
from comedores.services.comedor_service import ComedorService
from relevamientos.models import Relevamiento
from users.api_permissions import IsTerritorialComedorUser
from users.services_pwa import (
    get_territorial_comedor_provincia_ids,
    get_territorial_comedor_provincias,
)

MAX_IMAGENES_COMEDOR = 15
MAX_FIRMA_FILE_SIZE = 3 * 1024 * 1024  # 3 MB


class TerritorialUltimoRelevamientoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    estado = serializers.CharField(allow_null=True)
    fecha_visita = serializers.DateTimeField(allow_null=True)


class TerritorialComedorSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nombre = serializers.CharField()
    provincia = serializers.SerializerMethodField()
    municipio = serializers.SerializerMethodField()
    localidad = serializers.SerializerMethodField()
    calle = serializers.CharField(allow_null=True)
    numero = serializers.IntegerField(allow_null=True)
    barrio = serializers.CharField(allow_null=True)
    latitud = serializers.FloatField(allow_null=True)
    longitud = serializers.FloatField(allow_null=True)
    estado = serializers.CharField(allow_null=True)
    relevamientos = serializers.SerializerMethodField()

    def get_provincia(self, obj):
        return obj.provincia.nombre if obj.provincia_id else None

    def get_municipio(self, obj):
        return obj.municipio.nombre if obj.municipio_id else None

    def get_localidad(self, obj):
        return obj.localidad.nombre if obj.localidad_id else None

    def get_relevamientos(self, obj):
        relevamientos = getattr(obj, "relevamientos_territorial", None)
        if relevamientos is None:
            relevamientos = list(
                obj.relevamiento_set.all().order_by("-fecha_visita", "-id")
            )
        ultimo = relevamientos[0] if relevamientos else None
        return {
            "total": len(relevamientos),
            "ultimo": (
                TerritorialUltimoRelevamientoSerializer(ultimo).data if ultimo else None
            ),
        }


@extend_schema(tags=["Territorial"])
class TerritorialComedorViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """Comedores del alcance del territorial (por provincia).

    - ``GET /api/territorial/comedores/`` -> lista paginada (scope por provincia).
    - ``GET /api/territorial/comedores/{id}/`` -> detalle scopeado (404 fuera de
      scope).
    - ``POST /api/territorial/comedores/{id}/imagenes/`` -> subida de foto
      (multipart, campo ``imagen``).
    """

    serializer_class = TerritorialComedorSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsTerritorialComedorUser]

    def get_queryset(self):
        provincia_ids = get_territorial_comedor_provincia_ids(self.request.user)
        if not provincia_ids:
            return Comedor.objects.none()
        return (
            Comedor.objects.filter(provincia_id__in=provincia_ids)
            .select_related("provincia", "municipio", "localidad")
            .prefetch_related(
                Prefetch(
                    "relevamiento_set",
                    queryset=Relevamiento.objects.only(
                        "id", "estado", "fecha_visita", "comedor_id"
                    ).order_by("-fecha_visita", "-id"),
                    to_attr="relevamientos_territorial",
                )
            )
            .order_by("nombre", "id")
        )

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if isinstance(response.data, dict):
            response.data["provincias"] = get_territorial_comedor_provincias(
                request.user
            )
        return response

    def retrieve(self, request, *args, **kwargs):
        comedor = self.get_object()
        data = self.get_serializer(comedor).data
        # Precarga profunda del relevamiento (mismo shape que
        # GET /api/comedores/{id}/ -> relevamiento_actual_mobile.sections), pero
        # bajo la superficie scopeada del territorial. Reutiliza el builder del
        # ComedorDetailSerializer (que se autoconsulta si no hay prefetch).
        detail_serializer = ComedorDetailSerializer(context={"request": request})
        data["relevamiento_actual_mobile"] = (
            detail_serializer.get_relevamiento_actual_mobile(comedor)
        )
        return Response(data)

    def _serialize_imagenes(self, comedor, request):
        return [
            {
                "id": imagen.id,
                "url": (
                    request.build_absolute_uri(imagen.imagen.url)
                    if imagen.imagen
                    else None
                ),
            }
            for imagen in comedor.imagenes.all()
        ]

    @action(
        detail=True,
        methods=["post"],
        url_path="imagenes",
        parser_classes=[MultiPartParser, FormParser],
    )
    def imagenes(self, request, pk=None):
        # get_object() aplica el scope por provincia: 404 si el comedor no es del
        # territorial. Reutiliza el modelo ImagenComedor (origen="mobile").
        comedor = self.get_object()
        imagen = request.FILES.get("imagen")
        if not imagen:
            return Response(
                {"detail": "Debe adjuntar una imagen en el campo 'imagen'."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Idempotencia offline: si la PWA reintenta con el mismo client_uuid, no se
        # duplica; se devuelve el estado actual.
        client_uuid = (request.data.get("client_uuid") or "").strip() or None
        if client_uuid and comedor.imagenes.filter(client_uuid=client_uuid).exists():
            return Response(
                {"imagenes": self._serialize_imagenes(comedor, request)},
                status=status.HTTP_200_OK,
            )
        if comedor.imagenes.count() >= MAX_IMAGENES_COMEDOR:
            return Response(
                {
                    "detail": (
                        f"El espacio ya tiene el máximo de {MAX_IMAGENES_COMEDOR} "
                        "fotos."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        creado = ComedorService.create_imagenes(imagen, comedor.pk, origen="mobile")
        if isinstance(creado, dict):
            return Response(creado, status=status.HTTP_400_BAD_REQUEST)
        if client_uuid:
            creado.client_uuid = client_uuid
            try:
                creado.save(update_fields=["client_uuid"])
            except IntegrityError:
                # Carrera con otro reintento del mismo client_uuid: descarto el
                # duplicado recién creado y devuelvo lo que ya existe.
                creado.delete()
        return Response(
            {"imagenes": self._serialize_imagenes(comedor, request)},
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="firma",
        parser_classes=[MultiPartParser, FormParser],
    )
    def firma(self, request, pk=None):
        # Sube la firma como imagen y devuelve la URL, para guardarla como string
        # en excepcion.firma (relevamiento) o cierre.firma_* (seguimiento) vía el
        # PATCH. No se mezcla con las fotos del comedor (ImagenComedor).
        comedor = self.get_object()
        archivo = request.FILES.get("firma")
        if not archivo:
            return Response(
                {"detail": "Debe adjuntar la firma en el campo 'firma'."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        content_type = getattr(archivo, "content_type", "") or ""
        if not content_type.startswith("image/"):
            return Response(
                {"detail": "La firma debe ser una imagen."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if archivo.size > MAX_FIRMA_FILE_SIZE:
            return Response(
                {"detail": "La firma excede el tamaño máximo de 3 MB."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        path = default_storage.save(f"firmas/{comedor.id}/{archivo.name}", archivo)
        url = request.build_absolute_uri(default_storage.url(path))
        return Response({"url": url}, status=status.HTTP_201_CREATED)
