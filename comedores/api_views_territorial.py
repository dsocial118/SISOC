"""API mobile para usuarios territoriales de comedores (SISOC - Mobile).

El territorial (usuario SISOC con ``Profile.es_territorial_comedor=True``) lee
sus comedores asignados con scope por las provincias que tiene cargadas en
``TerritorialComedorProvincia``. Auth por DRF Token.
"""

from django.core.files.storage import default_storage
from django.db import IntegrityError, transaction
from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema
from rest_framework import generics, mixins, serializers, status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from comedores.api_serializers import ComedorDetailSerializer, NoSaveSerializer
from comedores.models import Comedor
from comedores.services.comedor_service import ComedorService
from core.utils import format_fecha_django
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
                        "origen": seguimiento.origen,
                        "asignado_desde_sisoc": seguimiento.asignado_desde_sisoc,
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

    def get_queryset(self):
        provincia_ids = get_territorial_comedor_provincia_ids(self.request.user)
        if not provincia_ids:
            return Comedor.objects.none()
        return (
            Comedor.objects.filter(provincia_id__in=provincia_ids)
            .select_related("provincia", "municipio", "localidad")
            .order_by("nombre", "id")
        )
