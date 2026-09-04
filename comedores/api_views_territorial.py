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
from rest_framework.views import APIView

from comedores.api_serializers import ComedorDetailSerializer, NoSaveSerializer
from comedores.models import Comedor
from comedores.services.comedor_service import ComedorService
from relevamientos.models import (
    MotivoExcepcionSeguimiento,
    PrimerSeguimiento,
    Relevamiento,
)
from users.api_permissions import IsTerritorialComedorUser
from users.services_pwa import get_territorial_comedor_provincias

MAX_IMAGENES_COMEDOR = 15
MAX_FIRMA_FILE_SIZE = 3 * 1024 * 1024  # 3 MB


class TerritorialUltimoRelevamientoSerializer(NoSaveSerializer):
    id = serializers.IntegerField()
    estado = serializers.CharField(allow_null=True)
    fecha_visita = serializers.DateTimeField(allow_null=True)
    territorial_user = serializers.IntegerField(
        source="territorial_user_id", allow_null=True
    )
    # Ciclo de validación del coordinador: la app muestra "Corregir y reenviar"
    # solo con "A subsanar" y lo oculta con "Validado".
    estado_validacion = serializers.CharField(allow_null=True)
    observaciones_coordinador = serializers.CharField(allow_null=True)
    fecha_revision_coordinador = serializers.DateTimeField(allow_null=True)


class TerritorialComedorSerializer(NoSaveSerializer):
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
    seguimientos = serializers.SerializerMethodField()

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
        # `items` expone TODOS los relevamientos del comedor (no solo `ultimo`),
        # para que la PWA liste el pendiente aunque exista uno finalizado más
        # reciente. `ultimo` se mantiene por compatibilidad.
        items = TerritorialUltimoRelevamientoSerializer(relevamientos, many=True).data
        ultimo = relevamientos[0] if relevamientos else None
        return {
            "total": len(relevamientos),
            "ultimo": (
                TerritorialUltimoRelevamientoSerializer(ultimo).data if ultimo else None
            ),
            "items": items,
        }

    def get_seguimientos(self, obj):
        # TODAS las instancias del ciclo de seguimiento de cada relevamiento del
        # comedor (primer, posteriores, virtual y actas de excepcion), ordenadas
        # por `numero_orden`. `id` = PK de la instancia: es el `sisoc_id` del
        # PATCH /api/relevamiento/seguimiento.
        relevamientos = getattr(obj, "relevamientos_territorial", None)
        if relevamientos is None:
            relevamientos = list(
                obj.relevamiento_set.all().prefetch_related("seguimientos")
            )
        items = []
        for relevamiento in relevamientos:
            seguimientos = sorted(
                relevamiento.seguimientos.all(),
                key=lambda seguimiento: seguimiento.numero_orden,
            )
            for seguimiento in seguimientos:
                items.append(
                    {
                        "id": seguimiento.id,
                        "tipo": seguimiento.tipo,
                        "numero_orden": seguimiento.numero_orden,
                        "estado": seguimiento.estado,
                        "id_relevamiento": relevamiento.id,
                        "gestionar_id": seguimiento.gestionar_id,
                        "fecha": seguimiento.fecha_hora,
                        "estado_validacion": seguimiento.estado_validacion,
                        "observaciones_coordinador": (
                            seguimiento.observaciones_coordinador
                        ),
                        "fecha_revision_coordinador": (
                            seguimiento.fecha_revision_coordinador
                        ),
                    }
                )
        return {"total": len(items), "items": items}


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
        # Visibilidad "solo asignados a mí": el territorial ve los comedores que
        # tienen al menos un relevamiento asignado a él (``territorial_user``), y
        # dentro de cada comedor solo sus relevamientos asignados. Reemplaza el
        # scope por provincia (un territorial ve exactamente su trabajo asignado,
        # aunque el comedor sea de otra provincia; la asignación se hace desde el
        # backoffice).
        user = self.request.user
        # ``Relevamiento.objects`` (manager soft-delete) ya excluye borrados en el
        # prefetch. Pero el JOIN ``relevamiento__...`` del filtro de comedores NO
        # aplica el manager, así que hay que excluir los borrados explícitamente;
        # de lo contrario un comedor cuyo único relevamiento asignado esté borrado
        # aparecería con ``items: []``.
        relevamientos_asignados = (
            Relevamiento.objects.filter(territorial_user=user)
            .prefetch_related("seguimientos")
            .order_by("-fecha_visita", "-id")
        )
        return (
            Comedor.objects.filter(
                relevamiento__territorial_user=user,
                relevamiento__deleted_at__isnull=True,
            )
            .distinct()
            .select_related("provincia", "municipio", "localidad")
            .prefetch_related(
                Prefetch(
                    "relevamiento_set",
                    queryset=relevamientos_asignados,
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

    def _serialize_imagenes(self, imagenes, request):
        return [
            {
                "id": imagen.id,
                "relevamiento": imagen.relevamiento_id,
                "seguimiento": imagen.seguimiento_id,
                "url": (
                    request.build_absolute_uri(imagen.imagen.url)
                    if imagen.imagen
                    else None
                ),
            }
            for imagen in imagenes
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

        # `sisoc_id` (opcional) = id del relevamiento (visita) al que se asocia la
        # foto. Si viene, el límite de 15 se cuenta por relevamiento; si no, es
        # comedor-level (compatibilidad).
        relevamiento_id = (request.data.get("sisoc_id") or "").strip() or None
        # `seguimiento_id` (opcional) = registro fotográfico del seguimiento.
        # Excluyente con `sisoc_id`: una foto cuelga del relevamiento o del
        # seguimiento, no de los dos.
        seguimiento_id = (request.data.get("seguimiento_id") or "").strip() or None
        if relevamiento_id is not None and seguimiento_id is not None:
            return Response(
                {
                    "detail": (
                        "Informe 'sisoc_id' (relevamiento) o 'seguimiento_id', "
                        "no ambos."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if relevamiento_id is not None:
            if not Relevamiento.objects.filter(
                id=relevamiento_id, comedor=comedor
            ).exists():
                return Response(
                    {
                        "detail": "El sisoc_id no corresponde a un relevamiento de este comedor."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        if seguimiento_id is not None:
            if not PrimerSeguimiento.objects.filter(
                id=seguimiento_id, id_relevamiento__comedor=comedor
            ).exists():
                return Response(
                    {
                        "detail": (
                            "El seguimiento_id no corresponde a un seguimiento "
                            "de este comedor."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        scope = comedor.imagenes.all()
        if relevamiento_id is not None:
            scope = scope.filter(relevamiento_id=relevamiento_id)
        elif seguimiento_id is not None:
            scope = scope.filter(seguimiento_id=seguimiento_id)

        # Idempotencia offline: si la PWA reintenta con el mismo client_uuid, no se
        # duplica; se devuelve el estado actual del scope.
        client_uuid = (request.data.get("client_uuid") or "").strip() or None
        if client_uuid and comedor.imagenes.filter(client_uuid=client_uuid).exists():
            return Response(
                {"imagenes": self._serialize_imagenes(scope, request)},
                status=status.HTTP_200_OK,
            )
        if scope.count() >= MAX_IMAGENES_COMEDOR:
            if relevamiento_id:
                destino = "este relevamiento"
            elif seguimiento_id:
                destino = "este seguimiento"
            else:
                destino = "el espacio"
            return Response(
                {
                    "detail": (
                        f"{destino} ya tiene el máximo de {MAX_IMAGENES_COMEDOR} "
                        "fotos."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        creado = ComedorService.create_imagenes(imagen, comedor.pk, origen="mobile")
        if isinstance(creado, dict):
            return Response(creado, status=status.HTTP_400_BAD_REQUEST)
        update_fields = []
        if relevamiento_id is not None:
            creado.relevamiento_id = relevamiento_id
            update_fields.append("relevamiento")
        if seguimiento_id is not None:
            creado.seguimiento_id = seguimiento_id
            update_fields.append("seguimiento")
        if client_uuid:
            creado.client_uuid = client_uuid
            update_fields.append("client_uuid")
        if update_fields:
            try:
                creado.save(update_fields=update_fields)
            except IntegrityError:
                # Carrera con otro reintento del mismo client_uuid: descarto el
                # duplicado recién creado y devuelvo lo que ya existe.
                creado.delete()
        scope = comedor.imagenes.all()
        if relevamiento_id is not None:
            scope = scope.filter(relevamiento_id=relevamiento_id)
        elif seguimiento_id is not None:
            scope = scope.filter(seguimiento_id=seguimiento_id)
        return Response(
            {"imagenes": self._serialize_imagenes(scope, request)},
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


@extend_schema(tags=["Territorial"])
class MotivosExcepcionSeguimientoView(APIView):
    """Catalogo de motivos del acta de excepcion de seguimiento (§18.3).

    Es un catalogo cerrado: el PATCH rechaza un motivo que no este en esta
    lista, asi que la app valida en cliente con estos mismos valores.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsTerritorialComedorUser]

    def get(self, request):
        items = list(
            MotivoExcepcionSeguimiento.objects.order_by("nombre").values("id", "nombre")
        )
        return Response({"items": items})
