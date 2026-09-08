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
from rest_framework import filters, generics, mixins, serializers, status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from comedores.api_serializers import ComedorDetailSerializer, NoSaveSerializer
from comedores.models import (
    Comedor,
    ComedorPwaCreateOperation,
    Programas,
    TipoDeComedor,
)
from comedores.services.comedor_service import ComedorService
from core.models import Localidad, Municipio, Provincia
from core.utils import format_fecha_django
from organizaciones.models import Organizacion
from relevamientos.models import (
    ActaComplementaria,
    MotivoExcepcionSeguimiento,
    PrestacionActaComplementaria,
    PrimerSeguimiento,
    Relevamiento,
)
from users.api_permissions import IsTerritorialComedorUser
from users.services_pwa import (
    get_territorial_comedor_provincia_ids,
    get_territorial_comedor_provincias,
)

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
    # De donde salio el registro: asignado por SISOC o autoactivado en la app.
    origen = serializers.CharField()
    asignado_desde_sisoc = serializers.BooleanField()


class TerritorialComedorSerializer(NoSaveSerializer):
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
                        "origen": seguimiento.origen,
                        "asignado_desde_sisoc": seguimiento.asignado_desde_sisoc,
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
            elif len(raw_comienzo) == 4 and raw_comienzo.isdigit():
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
    """Comedores asignados y operaciones territoriales de Gestionar.

    - ``GET /api/territorial/comedores/`` -> lista asignada al usuario.
    - ``GET /api/territorial/comedores/{id}/`` -> detalle asignado (404 fuera de
      su asignación).
    - ``POST /api/territorial/comedores/`` -> alta idempotente por ``client_uuid``.
    - ``PATCH /api/territorial/comedores/{id}/`` -> edición por provincia asignada.
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

    @staticmethod
    def _idempotency_conflict_response():
        return Response(
            {
                "detail": "La clave de idempotencia ya fue usada con otro payload.",
                "code": "idempotency_payload_conflict",
            },
            status=status.HTTP_409_CONFLICT,
        )

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
                    return self._idempotency_conflict_response()
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
                return self._idempotency_conflict_response()
            return Response(self._response_data(comedor), status=status.HTTP_200_OK)

        return Response(self._response_data(comedor), status=status.HTTP_201_CREATED)

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
        # Autocompletado en cadena (N17): snapshot del seguimiento inmediato
        # anterior al que el territorial va a completar, en el mismo formato de
        # secciones que `relevamiento_actual_mobile`.
        data["seguimiento_anterior_mobile"] = (
            detail_serializer.build_seguimiento_mobile(
                self._seguimiento_anterior(comedor)
            )
        )
        # Actas complementarias extraordinarias del comedor (N15).
        actas = list(comedor.actas_complementarias.prefetch_related("prestaciones"))
        data["actas_complementarias"] = {
            "total": len(actas),
            "items": [self._serialize_acta(acta) for acta in actas],
        }
        return Response(data)

    def _seguimiento_anterior(self, comedor):
        """La instancia previa a la que está pendiente de completar.

        Se toma la pendiente (la de mayor ``numero_orden`` que todavía no está
        completa) y se devuelve la anterior a ella. Si no hay ninguna pendiente,
        se devuelve la última del ciclo, que es de donde conviene prellenar.
        """
        seguimientos = sorted(
            PrimerSeguimiento.objects.filter(
                id_relevamiento__comedor=comedor
            ).select_related(*PrimerSeguimiento.BLOQUES_ONE_TO_ONE),
            key=lambda seguimiento: seguimiento.numero_orden,
        )
        if not seguimientos:
            return None

        pendientes = [
            seguimiento
            for seguimiento in seguimientos
            if seguimiento.estado != PrimerSeguimiento.ESTADO_COMPLETO
        ]
        if not pendientes:
            return seguimientos[-1]

        orden_pendiente = pendientes[-1].numero_orden
        anteriores = [
            seguimiento
            for seguimiento in seguimientos
            if seguimiento.numero_orden < orden_pendiente
        ]
        return anteriores[-1] if anteriores else None

    # ------------------------------------------------------------------ #
    # Altas desde la app (N15 / N18)
    # ------------------------------------------------------------------ #
    # El scope de lectura es "asignado a mi", pero para CREAR hace falta poder
    # actuar sobre un comedor de la zona que todavia no tiene nada asignado. Por
    # eso estas acciones resuelven el comedor por PROVINCIA y no con
    # get_object(), que exige asignacion previa.

    def _comedor_de_mi_zona(self):
        provincia_ids = get_territorial_comedor_provincia_ids(self.request.user)
        return Comedor.objects.filter(
            pk=self.kwargs["pk"], provincia_id__in=provincia_ids
        ).first()

    def partial_update(self, request, *args, **kwargs):
        # La edición sigue la misma regla provincial que las altas N15/N18: no
        # depende de una asignación previa de relevamiento.
        comedor = self._comedor_de_mi_zona()
        if comedor is None:
            return self._fuera_de_zona()
        serializer = self.get_serializer(comedor, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(self._response_data(comedor), status=status.HTTP_200_OK)

    @staticmethod
    def _fuera_de_zona():
        return Response(
            {"detail": "El comedor no pertenece a su zona."},
            status=status.HTTP_404_NOT_FOUND,
        )

    @staticmethod
    def _leer_client_uuid(request):
        return (request.data.get("client_uuid") or "").strip() or None

    @staticmethod
    def _falta_client_uuid():
        return Response(
            {"detail": "Falta 'client_uuid'."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @staticmethod
    def _fecha_invalida(campo):
        return Response(
            {"detail": f"'{campo}' debe tener formato dd/mm/YYYY HH:MM."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=True, methods=["post"], url_path="relevamientos")
    def crear_relevamiento(  # pylint: disable=too-many-return-statements
        self, request, pk=None
    ):
        """Autoactivacion de un relevamiento sobre un comedor de la zona."""
        comedor = self._comedor_de_mi_zona()
        if comedor is None:
            return self._fuera_de_zona()

        client_uuid = self._leer_client_uuid(request)
        if not client_uuid:
            return self._falta_client_uuid()

        # Idempotencia: el mismo uuid devuelve el registro ya creado. Se busca con
        # `all_objects` porque el indice UNIQUE de client_uuid incluye a los
        # soft-deleted: si SISOC borro logicamente el relevamiento y la cola
        # offline reintenta el mismo uuid, con `objects` no lo encontrariamos,
        # el INSERT chocaria contra el UNIQUE y el reintento daria 500 para siempre.
        existente = Relevamiento.all_objects.filter(client_uuid=client_uuid).first()
        if existente is not None:
            return Response(
                self._serialize_relevamiento_creado(existente),
                status=status.HTTP_200_OK,
            )

        # `validate_relevamientos_activos` no permite dos activos en el mismo
        # comedor: en vez de un 500 opaco se devuelve el id del activo para que
        # la app lo complete en lugar de crear otro.
        activo = Relevamiento.objects.filter(
            comedor=comedor, estado__in=["Pendiente", "Visita pendiente"]
        ).first()
        if activo is not None:
            return Response(
                {
                    "detail": "El comedor ya tiene un relevamiento activo.",
                    "relevamiento_id": activo.id,
                },
                status=status.HTTP_409_CONFLICT,
            )

        relevamiento = Relevamiento(
            comedor=comedor,
            estado="Visita pendiente",
            territorial_user=request.user,
            origen=Relevamiento.ORIGEN_APP,
            asignado_desde_sisoc=False,
            client_uuid=client_uuid,
        )
        fecha_visita = (request.data.get("fecha_visita") or "").strip() or None
        if fecha_visita:
            try:
                relevamiento.fecha_visita = format_fecha_django(fecha_visita)
            except (ValueError, TypeError):
                return self._fecha_invalida("fecha_visita")
        try:
            relevamiento.save()
        except IntegrityError:
            # Carrera con otro reintento del mismo uuid (o uuid de uno borrado).
            existente = Relevamiento.all_objects.filter(client_uuid=client_uuid).first()
            if existente is None:
                raise
            return Response(
                self._serialize_relevamiento_creado(existente),
                status=status.HTTP_200_OK,
            )

        return Response(
            self._serialize_relevamiento_creado(relevamiento),
            status=status.HTTP_201_CREATED,
        )

    @staticmethod
    def _serialize_relevamiento_creado(relevamiento):
        return {
            "id": relevamiento.id,
            "comedor": relevamiento.comedor_id,
            "estado": relevamiento.estado,
            "fecha_visita": relevamiento.fecha_visita,
            "territorial_user": relevamiento.territorial_user_id,
            "origen": relevamiento.origen,
            "asignado_desde_sisoc": relevamiento.asignado_desde_sisoc,
            "client_uuid": relevamiento.client_uuid,
        }

    @action(detail=True, methods=["post"], url_path="seguimientos")
    def crear_seguimiento(  # pylint: disable=too-many-return-statements
        self, request, pk=None
    ):
        """Autoactivacion de una instancia del ciclo de seguimiento."""
        comedor = self._comedor_de_mi_zona()
        if comedor is None:
            return self._fuera_de_zona()

        client_uuid = self._leer_client_uuid(request)
        if not client_uuid:
            return self._falta_client_uuid()

        existente = PrimerSeguimiento.objects.filter(client_uuid=client_uuid).first()
        if existente is not None:
            return Response(
                self._serialize_seguimiento_creado(existente),
                status=status.HTTP_200_OK,
            )

        tipo = (request.data.get("tipo") or "").strip()
        if tipo not in PrimerSeguimiento.TIPOS_CREABLES_DESDE_APP:
            return Response(
                {
                    "detail": (
                        "'tipo' invalido. Validos: "
                        f"{list(PrimerSeguimiento.TIPOS_CREABLES_DESDE_APP)}."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # El ciclo cuelga del relevamiento ancla del comedor.
        relevamiento = (
            Relevamiento.objects.filter(comedor=comedor)
            .order_by("-fecha_visita", "-id")
            .first()
        )
        if relevamiento is None:
            return Response(
                {
                    "detail": (
                        "El comedor no tiene un relevamiento del cual colgar el "
                        "seguimiento."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        ultimo_orden = (
            PrimerSeguimiento.objects.filter(id_relevamiento=relevamiento)
            .order_by("-numero_orden")
            .values_list("numero_orden", flat=True)
            .first()
        ) or 0

        seguimiento = PrimerSeguimiento(
            id_relevamiento=relevamiento,
            tipo=tipo,
            numero_orden=ultimo_orden + 1,
            estado=PrimerSeguimiento.ESTADO_ASIGNADO,
            origen=PrimerSeguimiento.ORIGEN_APP,
            asignado_desde_sisoc=False,
            client_uuid=client_uuid,
        )
        try:
            seguimiento.save()
        except IntegrityError:
            existente = PrimerSeguimiento.objects.filter(
                client_uuid=client_uuid
            ).first()
            if existente is None:
                raise
            return Response(
                self._serialize_seguimiento_creado(existente),
                status=status.HTTP_200_OK,
            )

        return Response(
            self._serialize_seguimiento_creado(seguimiento),
            status=status.HTTP_201_CREATED,
        )

    @staticmethod
    def _serialize_seguimiento_creado(seguimiento):
        return {
            "id": seguimiento.id,
            "id_relevamiento": seguimiento.id_relevamiento_id,
            "tipo": seguimiento.tipo,
            "numero_orden": seguimiento.numero_orden,
            "estado": seguimiento.estado,
            "origen": seguimiento.origen,
            "asignado_desde_sisoc": seguimiento.asignado_desde_sisoc,
            "client_uuid": seguimiento.client_uuid,
        }

    @action(detail=True, methods=["post"], url_path="actas-complementarias")
    def crear_acta_complementaria(  # pylint: disable=too-many-return-statements
        self, request, pk=None
    ):
        """Acta complementaria extraordinaria (N15): cambio de prestacion."""
        comedor = self._comedor_de_mi_zona()
        if comedor is None:
            return self._fuera_de_zona()

        client_uuid = self._leer_client_uuid(request)
        if not client_uuid:
            return self._falta_client_uuid()

        existente = ActaComplementaria.objects.filter(client_uuid=client_uuid).first()
        if existente is not None:
            return Response(self._serialize_acta(existente), status=status.HTTP_200_OK)

        prestaciones = request.data.get("prestaciones") or []
        if not isinstance(prestaciones, list) or any(
            not isinstance(fila, dict) for fila in prestaciones
        ):
            return Response(
                {"detail": "'prestaciones' debe ser una lista de objetos."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        acta = ActaComplementaria(
            comedor=comedor,
            tecnico=request.user,
            observaciones=(request.data.get("observaciones") or "").strip() or None,
            firma=(request.data.get("firma") or "").strip() or None,
            origen=ActaComplementaria.ORIGEN_APP,
            asignado_desde_sisoc=False,
            client_uuid=client_uuid,
        )
        fecha_hora = (request.data.get("fecha_hora") or "").strip() or None
        if fecha_hora:
            try:
                acta.fecha_hora = format_fecha_django(fecha_hora)
            except (ValueError, TypeError):
                return self._fecha_invalida("fecha_hora")

        try:
            with transaction.atomic():
                acta.save()
                for fila in prestaciones:
                    PrestacionActaComplementaria.objects.create(
                        acta=acta,
                        dias_prestacion=fila.get("dias_prestacion"),
                        tipo_prestacion=fila.get("tipo_prestacion"),
                        cantidad_actual=fila.get("cantidad_actual"),
                        cantidad_espera=fila.get("cantidad_espera"),
                    )
        except IntegrityError:
            existente = ActaComplementaria.objects.filter(
                client_uuid=client_uuid
            ).first()
            if existente is None:
                raise
            return Response(self._serialize_acta(existente), status=status.HTTP_200_OK)

        return Response(self._serialize_acta(acta), status=status.HTTP_201_CREATED)

    @staticmethod
    def _serialize_acta(acta):
        return {
            "id": acta.id,
            "comedor": acta.comedor_id,
            "tecnico": acta.tecnico_id,
            "fecha_hora": acta.fecha_hora,
            "observaciones": acta.observaciones,
            "firma": acta.firma,
            "origen": acta.origen,
            "client_uuid": acta.client_uuid,
            "prestaciones": [
                {
                    "id": fila.id,
                    "dias_prestacion": fila.dias_prestacion,
                    "tipo_prestacion": fila.tipo_prestacion,
                    "cantidad_actual": fila.cantidad_actual,
                    "cantidad_espera": fila.cantidad_espera,
                }
                for fila in acta.prestaciones.all()
            ],
        }

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

    @staticmethod
    def _resolver_destino_foto(request, comedor):
        """A que cuelga la foto: relevamiento (`sisoc_id`) o seguimiento
        (`seguimiento_id`), excluyentes. Devuelve (relevamiento_id,
        seguimiento_id, error_response)."""
        relevamiento_id = (request.data.get("sisoc_id") or "").strip() or None
        seguimiento_id = (request.data.get("seguimiento_id") or "").strip() or None
        if relevamiento_id is not None and seguimiento_id is not None:
            return (
                None,
                None,
                Response(
                    {
                        "detail": (
                            "Informe 'sisoc_id' (relevamiento) o 'seguimiento_id', "
                            "no ambos."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                ),
            )
        if (
            relevamiento_id is not None
            and not Relevamiento.objects.filter(
                id=relevamiento_id, comedor=comedor
            ).exists()
        ):
            return (
                None,
                None,
                Response(
                    {
                        "detail": "El sisoc_id no corresponde a un relevamiento de este comedor."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                ),
            )
        if (
            seguimiento_id is not None
            and not PrimerSeguimiento.objects.filter(
                id=seguimiento_id, id_relevamiento__comedor=comedor
            ).exists()
        ):
            return (
                None,
                None,
                Response(
                    {
                        "detail": (
                            "El seguimiento_id no corresponde a un seguimiento "
                            "de este comedor."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                ),
            )
        return relevamiento_id, seguimiento_id, None

    @staticmethod
    def _scope_fotos(comedor, relevamiento_id, seguimiento_id):
        """Fotos sobre las que se cuenta el tope de 15 y se responde."""
        scope = comedor.imagenes.all()
        if relevamiento_id is not None:
            return scope.filter(relevamiento_id=relevamiento_id)
        if seguimiento_id is not None:
            return scope.filter(seguimiento_id=seguimiento_id)
        return scope

    @action(
        detail=True,
        methods=["post"],
        url_path="imagenes",
        parser_classes=[MultiPartParser, FormParser],
    )
    def imagenes(self, request, pk=None):
        # get_object() aplica el scope de lectura: 404 si el comedor no es del
        # territorial. Reutiliza el modelo ImagenComedor (origen="mobile").
        comedor = self.get_object()
        imagen = request.FILES.get("imagen")
        if not imagen:
            return Response(
                {"detail": "Debe adjuntar una imagen en el campo 'imagen'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        relevamiento_id, seguimiento_id, error = self._resolver_destino_foto(
            request, comedor
        )
        if error is not None:
            return error
        scope = self._scope_fotos(comedor, relevamiento_id, seguimiento_id)

        # Idempotencia offline: si la PWA reintenta con el mismo client_uuid, no se
        # duplica; se devuelve el estado actual del scope.
        client_uuid = (request.data.get("client_uuid") or "").strip() or None
        if client_uuid and comedor.imagenes.filter(client_uuid=client_uuid).exists():
            return Response(
                {"imagenes": self._serialize_imagenes(scope, request)},
                status=status.HTTP_200_OK,
            )
        if scope.count() >= MAX_IMAGENES_COMEDOR:
            destino = "el espacio"
            if relevamiento_id:
                destino = "este relevamiento"
            elif seguimiento_id:
                destino = "este seguimiento"
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
        scope = self._scope_fotos(comedor, relevamiento_id, seguimiento_id)
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


class TerritorialComedorZonaSerializer(NoSaveSerializer):
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

    def get_provincia(self, obj):
        return obj.provincia.nombre if obj.provincia_id else None

    def get_municipio(self, obj):
        return obj.municipio.nombre if obj.municipio_id else None

    def get_localidad(self, obj):
        return obj.localidad.nombre if obj.localidad_id else None


@extend_schema(tags=["Territorial"])
class TerritorialComedorZonaListView(generics.ListAPIView):
    """``GET /api/territorial/comedores-zona/`` - comedores de MI ZONA.

    Devuelve los comedores de las provincias del territorial, para que pueda
    activar trabajo sin esperar asignacion (N18). Es un endpoint aparte y con
    serializer liviano a proposito: `/territorial/comedores/` sigue siendo
    "asignados a mi", y meter aca los relevamientos/seguimientos reproduciria la
    lentitud que tenia el listado por provincia.
    """

    serializer_class = TerritorialComedorZonaSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsTerritorialComedorUser]
    # ``?search=`` por nombre / localidad / municipio: con miles de comedores por
    # provincia el filtro solo sobre lo ya paginado en la app es insuficiente.
    filter_backends = [filters.SearchFilter]
    search_fields = ["nombre", "localidad__nombre", "municipio__nombre"]

    def get_queryset(self):
        provincia_ids = get_territorial_comedor_provincia_ids(self.request.user)
        if not provincia_ids:
            return Comedor.objects.none()
        return (
            Comedor.objects.filter(provincia_id__in=provincia_ids)
            .select_related("provincia", "municipio", "localidad")
            .order_by("nombre", "id")
        )
