"""API mobile para usuarios territoriales de comedores (SISOC - Mobile).

El territorial (usuario SISOC con ``Profile.es_territorial_comedor=True``) lee
sus comedores asignados con scope por las provincias que tiene cargadas en
``TerritorialComedorProvincia``. Auth por DRF Token.
"""

import hashlib
import json
from datetime import date

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.files.storage import default_storage
from django.db import IntegrityError, transaction
from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from comedores.api_serializers import ComedorDetailSerializer
from comedores.models import (
    Comedor,
    ComedorPwaCreateOperation,
    Programas,
    TipoDeComedor,
)
from comedores.services.comedor_service import ComedorService
from core.models import Localidad, Municipio, Provincia
from organizaciones.models import Organizacion
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
    tipo = serializers.SerializerMethodField()
    programa = serializers.SerializerMethodField()
    organizacion = serializers.SerializerMethodField()
    comienzo = serializers.IntegerField(allow_null=True)
    provincia = serializers.SerializerMethodField()
    municipio = serializers.SerializerMethodField()
    localidad = serializers.SerializerMethodField()
    calle = serializers.CharField(allow_null=True)
    numero = serializers.IntegerField(allow_null=True)
    entre_calle_1 = serializers.CharField(allow_null=True)
    entre_calle_2 = serializers.CharField(allow_null=True)
    barrio = serializers.CharField(allow_null=True)
    codigo_postal = serializers.IntegerField(allow_null=True)
    latitud = serializers.FloatField(allow_null=True)
    longitud = serializers.FloatField(allow_null=True)
    estado = serializers.CharField(allow_null=True)
    relevamientos = serializers.SerializerMethodField()
    seguimientos = serializers.SerializerMethodField()

    def get_provincia(self, obj):
        return obj.provincia.nombre if obj.provincia_id else None

    def get_tipo(self, obj):
        return obj.tipocomedor.nombre if obj.tipocomedor_id else None

    def get_programa(self, obj):
        return obj.programa.nombre if obj.programa_id else None

    def get_organizacion(self, obj):
        return obj.organizacion.nombre if obj.organizacion_id else None

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
        # Primer seguimiento por comedor = el `primer_seguimiento` (OneToOne) de
        # cada relevamiento del comedor. `id` = PK del PrimerSeguimiento (sirve como
        # `sisoc_id` en PATCH /api/relevamiento/primer-seguimiento).
        relevamientos = getattr(obj, "relevamientos_territorial", None)
        if relevamientos is None:
            relevamientos = list(
                obj.relevamiento_set.all().select_related("primer_seguimiento")
            )
        items = []
        for relevamiento in relevamientos:
            try:
                seguimiento = relevamiento.primer_seguimiento
            except ObjectDoesNotExist:
                seguimiento = None
            if seguimiento is None:
                continue
            items.append(
                {
                    "id": seguimiento.id,
                    "estado": seguimiento.estado,
                    "id_relevamiento": relevamiento.id,
                    "gestionar_id": seguimiento.gestionar_id,
                    "fecha": seguimiento.fecha_hora,
                }
            )
        return {"total": len(items), "items": items}


class TerritorialComedorWriteSerializer(serializers.Serializer):
    """Contrato de escritura de Gestionar, separado del detalle web de SISOC."""

    client_uuid = serializers.CharField(max_length=100, write_only=True, required=False)
    nombre = serializers.CharField(max_length=255)
    tipo = serializers.CharField(max_length=255)
    programa = serializers.CharField(max_length=255, required=False, allow_blank=True)
    organizacion = serializers.CharField(
        max_length=255, required=False, allow_blank=True
    )
    comienzo = serializers.CharField(max_length=10, required=False, allow_blank=True)
    provincia = serializers.CharField(max_length=255, required=False)
    municipio = serializers.CharField(max_length=255, required=False, allow_blank=True)
    localidad = serializers.CharField(max_length=255, required=False, allow_blank=True)
    calle = serializers.CharField(max_length=255, required=False, allow_blank=True)
    numero = serializers.IntegerField(required=False, allow_null=True)
    entre_calle_1 = serializers.CharField(
        max_length=255, required=False, allow_blank=True
    )
    entre_calle_2 = serializers.CharField(
        max_length=255, required=False, allow_blank=True
    )
    barrio = serializers.CharField(max_length=255, required=False, allow_blank=True)
    codigo_postal = serializers.IntegerField(required=False, allow_null=True)
    latitud = serializers.FloatField(required=False, allow_null=True)
    longitud = serializers.FloatField(required=False, allow_null=True)

    @staticmethod
    def _single_by_name(model, value, field, **filters):
        if value in (None, ""):
            return None
        matches = list(
            model.objects.filter(nombre__iexact=value, **filters).order_by("id")[:2]
        )
        if len(matches) != 1:
            raise serializers.ValidationError(
                {field: "Debe indicar un valor existente y no ambiguo en SISOC."}
            )
        return matches[0]

    def validate(self, attrs):
        if self.instance and "client_uuid" in attrs:
            raise serializers.ValidationError(
                {"client_uuid": "Solo se acepta al crear un comedor."}
            )

        scope_ids = set(
            get_territorial_comedor_provincia_ids(self.context["request"].user)
        )
        province_name = attrs.pop("provincia", None)
        provincia = None
        if province_name is not None:
            provincia = self._single_by_name(Provincia, province_name, "provincia")
        elif self.instance:
            provincia = self.instance.provincia
        else:
            raise serializers.ValidationError(
                {"provincia": "Este campo es obligatorio."}
            )

        if provincia is None or provincia.id not in scope_ids:
            raise PermissionDenied(
                "La provincia indicada no pertenece a su alcance territorial."
            )
        attrs["provincia"] = provincia

        if "tipo" in attrs:
            attrs["tipocomedor"] = self._single_by_name(
                TipoDeComedor, attrs.pop("tipo"), "tipo"
            )
        if "programa" in attrs:
            attrs["programa"] = self._single_by_name(
                Programas, attrs["programa"], "programa"
            )
        if "organizacion" in attrs:
            attrs["organizacion"] = self._single_by_name(
                Organizacion, attrs["organizacion"], "organizacion"
            )

        municipio_was_provided = "municipio" in attrs
        localidad_was_provided = "localidad" in attrs
        if municipio_was_provided:
            attrs["municipio"] = self._single_by_name(
                Municipio,
                attrs["municipio"],
                "municipio",
                provincia=provincia,
            )
        municipio = attrs.get(
            "municipio", self.instance.municipio if self.instance else None
        )
        if localidad_was_provided:
            if attrs["localidad"] and municipio is None:
                raise serializers.ValidationError(
                    {"localidad": "Requiere un municipio válido."}
                )
            attrs["localidad"] = self._single_by_name(
                Localidad,
                attrs["localidad"],
                "localidad",
                municipio=municipio,
            )

        if self.instance:
            if provincia.pk != self.instance.provincia_id and not municipio_was_provided:
                raise serializers.ValidationError(
                    {
                        "municipio": (
                            "Debe indicarlo al cambiar la provincia para conservar "
                            "la jerarquía territorial."
                        )
                    }
                )
            municipio_id = getattr(municipio, "pk", None)
            if (
                municipio_was_provided
                and municipio_id != self.instance.municipio_id
                and not localidad_was_provided
            ):
                raise serializers.ValidationError(
                    {
                        "localidad": (
                            "Debe indicarla o limpiarla al cambiar el municipio."
                        )
                    }
                )

        if "comienzo" in attrs:
            raw_comienzo = attrs["comienzo"]
            if not raw_comienzo:
                attrs["comienzo"] = None
            else:
                if len(raw_comienzo) == 4 and raw_comienzo.isdigit():
                    attrs["comienzo"] = int(raw_comienzo)
                else:
                    try:
                        attrs["comienzo"] = date.fromisoformat(raw_comienzo).year
                    except ValueError as exc:
                        raise serializers.ValidationError(
                            {"comienzo": "Use YYYY o una fecha ISO YYYY-MM-DD."}
                        ) from exc

        return attrs

    @staticmethod
    def _validate_model(instance):
        try:
            instance.full_clean()
        except ValidationError as exc:
            raise serializers.ValidationError(exc.message_dict) from exc

    def create(self, validated_data):
        validated_data.pop("client_uuid", None)
        instance = Comedor(**validated_data)
        self._validate_model(instance)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        validated_data.pop("client_uuid", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        self._validate_model(instance)
        instance.save()
        return instance


@extend_schema(tags=["Territorial"])
class TerritorialComedorViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """Comedores del alcance del territorial (por provincia).

    - ``GET /api/territorial/comedores/`` -> lista paginada (scope por provincia).
    - ``GET /api/territorial/comedores/{id}/`` -> detalle scopeado (404 fuera de
      scope).
    - ``POST /api/territorial/comedores/`` -> alta idempotente por ``client_uuid``.
    - ``PATCH /api/territorial/comedores/{id}/`` -> edición scopeada.
    - ``POST /api/territorial/comedores/{id}/imagenes/`` -> subida de foto
      (multipart, campo ``imagen``).
    """

    serializer_class = TerritorialComedorSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsTerritorialComedorUser]
    http_method_names = ["get", "post", "patch", "head", "options"]
    _CREATE_PAYLOAD_FIELDS = (
        "nombre",
        "tipo",
        "programa",
        "organizacion",
        "comienzo",
        "provincia",
        "municipio",
        "localidad",
        "calle",
        "numero",
        "entre_calle_1",
        "entre_calle_2",
        "barrio",
        "codigo_postal",
        "latitud",
        "longitud",
    )

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return TerritorialComedorWriteSerializer
        return TerritorialComedorSerializer

    def _response_data(self, comedor):
        return TerritorialComedorSerializer(
            comedor, context=self.get_serializer_context()
        ).data

    def _replay_is_authorized(self, operation):
        comedor = operation.comedor
        scope_ids = set(get_territorial_comedor_provincia_ids(self.request.user))
        if not comedor or comedor.provincia_id not in scope_ids:
            raise PermissionDenied(
                "La operación ya no pertenece a su alcance territorial actual."
            )
        return comedor

    @classmethod
    def _request_payload_digest(cls, payload):
        """Huella durable del request, independiente de catálogos renombrables."""
        normalized = {}
        for field in cls._CREATE_PAYLOAD_FIELDS:
            value = payload.get(field)
            normalized[field] = value.strip() if isinstance(value, str) else value
        return hashlib.sha256(
            json.dumps(
                normalized,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()

    def create(self, request, *args, **kwargs):
        client_uuid = request.data.get("client_uuid")
        if client_uuid:
            payload_digest = self._request_payload_digest(request.data)
            operation = (
                ComedorPwaCreateOperation.objects.select_related("comedor")
                .filter(user=request.user, client_uuid=client_uuid)
                .first()
            )
            if operation is not None:
                comedor = self._replay_is_authorized(operation)
                if operation.payload_digest != payload_digest:
                    return Response(
                        {
                            "detail": (
                                "La clave de idempotencia ya fue usada con otro payload."
                            ),
                            "code": "idempotency_payload_conflict",
                        },
                        status=status.HTTP_409_CONFLICT,
                    )
                return Response(self._response_data(comedor), status=status.HTTP_200_OK)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        client_uuid = serializer.validated_data.get("client_uuid")
        if not client_uuid:
            raise serializers.ValidationError(
                {"client_uuid": "Este campo es obligatorio para crear un comedor."}
            )

        payload_digest = self._request_payload_digest(request.data)

        try:
            with transaction.atomic():
                operation = ComedorPwaCreateOperation.objects.create(
                    user=request.user,
                    client_uuid=client_uuid,
                    payload_digest=payload_digest,
                )
                comedor = serializer.save()
                operation.comedor = comedor
                operation.save(update_fields=["comedor"])
        except IntegrityError:
            operation = (
                ComedorPwaCreateOperation.objects.select_related("comedor")
                .filter(user=request.user, client_uuid=client_uuid)
                .first()
            )
            if operation is None:
                raise
            comedor = self._replay_is_authorized(operation)
            if operation.payload_digest != payload_digest:
                return Response(
                    {
                        "detail": (
                            "La clave de idempotencia ya fue usada con otro payload."
                        ),
                        "code": "idempotency_payload_conflict",
                    },
                    status=status.HTTP_409_CONFLICT,
                )
            return Response(self._response_data(comedor), status=status.HTTP_200_OK)

        return Response(self._response_data(comedor), status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        comedor = self.get_object()
        serializer = self.get_serializer(comedor, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(self._response_data(comedor), status=status.HTTP_200_OK)

    def get_queryset(self):
        provincia_ids = get_territorial_comedor_provincia_ids(self.request.user)
        if not provincia_ids:
            return Comedor.objects.none()
        return (
            Comedor.objects.filter(provincia_id__in=provincia_ids)
            .select_related(
                "provincia",
                "municipio",
                "localidad",
                "tipocomedor",
                "programa",
                "organizacion",
            )
            .prefetch_related(
                Prefetch(
                    "relevamiento_set",
                    queryset=Relevamiento.objects.select_related(
                        "primer_seguimiento"
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

    def _serialize_imagenes(self, imagenes, request):
        return [
            {
                "id": imagen.id,
                "relevamiento": imagen.relevamiento_id,
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
        if relevamiento_id is not None:
            if not Relevamiento.objects.filter(
                id=relevamiento_id, comedor=comedor
            ).exists():
                return Response(
                    {"detail": "El sisoc_id no corresponde a un relevamiento de este comedor."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        scope = comedor.imagenes.all()
        if relevamiento_id is not None:
            scope = scope.filter(relevamiento_id=relevamiento_id)

        # Idempotencia offline: si la PWA reintenta con el mismo client_uuid, no se
        # duplica; se devuelve el estado actual del scope.
        client_uuid = (request.data.get("client_uuid") or "").strip() or None
        if client_uuid and comedor.imagenes.filter(client_uuid=client_uuid).exists():
            return Response(
                {"imagenes": self._serialize_imagenes(scope, request)},
                status=status.HTTP_200_OK,
            )
        if scope.count() >= MAX_IMAGENES_COMEDOR:
            destino = "este relevamiento" if relevamiento_id else "el espacio"
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
