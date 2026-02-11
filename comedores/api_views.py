from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from comedores.api_serializers import (
    APROBADAS_FIELDS,
    ComedorDetailSerializer,
    DocumentoComedorSerializer,
    InformeTecnicoPrestacionSerializer,
    NominaCreateSerializer,
    NominaSerializer,
    NominaUpdateSerializer,
)
from comedores.models import (
    AuditComedorPrograma,
    Comedor,
    ImagenComedor,
    Nomina,
    Observacion,
)
from core.api_auth import HasAPIKey
from django.core.paginator import Paginator
from django.http import FileResponse, Http404
import calendar
from datetime import date

from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.timezone import make_aware
from django.db.models import Prefetch
from django.db.models.fields.files import FieldFile
from intervenciones.models.intervenciones import Intervencion
from relevamientos.models import ClasificacionComedor, Relevamiento
from rendicioncuentasfinal.models import DocumentoRendicionFinal
from rendicioncuentasmensual.models import RendicionCuentaMensual
from comedores.services.comedor_service import ComedorService
from comedores.forms.comedor_form import CiudadanoFormParaNomina, NominaExtraForm
from admisiones.models.admisiones import InformeTecnico


@extend_schema(tags=["Comedores"])
class ComedorDetailViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = ComedorDetailSerializer
    authentication_classes = []
    permission_classes = [HasAPIKey]
    http_method_names = ["get", "post", "head", "options"]

    def list(self, request, *args, **kwargs):
        return Response(
            {"detail": "Listado no disponible en este endpoint."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    # Los métodos de documentos se definen más abajo con su implementación real.

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

    def _coerce_datetime(self, value):
        if not value:
            return None
        if timezone.is_naive(value):
            return make_aware(value)
        return value

    def _build_absolute_url(self, request, field):
        if not isinstance(field, FieldFile) or not field:
            return None
        url = field.url
        return request.build_absolute_uri(url) if request else url

    def _file_path_from_field(self, field):
        if not isinstance(field, FieldFile) or not field:
            return None
        try:
            return field.path
        except (ValueError, NotImplementedError):
            return None

    def _parse_period_date(self, value, *, is_end=False):
        if not value:
            return None
        parsed = parse_date(value)
        if parsed:
            return parsed
        try:
            parts = value.split("-")
            if len(parts) == 2:
                year = int(parts[0])
                month = int(parts[1])
                if is_end:
                    last_day = calendar.monthrange(year, month)[1]
                    return date(year, month, last_day)
                return date(year, month, 1)
        except (TypeError, ValueError, IndexError):
            return None
        return None

    def _collect_documentos(self, comedor, request):
        documentos = []

        if comedor.foto_legajo:
            documentos.append(
                {
                    "id": f"comedor-foto-legajo-{comedor.id}",
                    "origen": "comedores",
                    "tipo": "foto_legajo",
                    "nombre": comedor.foto_legajo.name,
                    "fecha": comedor.fecha_creacion,
                    "url": self._build_absolute_url(request, comedor.foto_legajo),
                    "path": self._file_path_from_field(comedor.foto_legajo),
                }
            )

        imagenes = getattr(comedor, "imagenes_optimized", None) or comedor.imagenes.all()
        for imagen in imagenes:
            documentos.append(
                {
                    "id": f"comedor-imagen-{imagen.id}",
                    "origen": "comedores",
                    "tipo": "imagen_comedor",
                    "nombre": imagen.imagen.name if imagen.imagen else None,
                    "fecha": None,
                    "url": self._build_absolute_url(request, imagen.imagen),
                    "path": self._file_path_from_field(imagen.imagen),
                }
            )

        intervenciones = (
            Intervencion.objects.filter(comedor=comedor, documentacion__isnull=False)
            .only("id", "documentacion", "fecha")
            .order_by("-fecha", "-id")
        )
        for intervencion in intervenciones:
            documentos.append(
                {
                    "id": f"intervencion-{intervencion.id}",
                    "origen": "intervenciones",
                    "tipo": "documentacion_intervencion",
                    "nombre": (
                        intervencion.documentacion.name
                        if intervencion.documentacion
                        else None
                    ),
                    "fecha": self._coerce_datetime(intervencion.fecha),
                    "url": self._build_absolute_url(
                        request, intervencion.documentacion
                    ),
                    "path": self._file_path_from_field(intervencion.documentacion),
                }
            )

        documentos_rendicion_final = (
            DocumentoRendicionFinal.objects.filter(
                rendicion_final__comedor=comedor, documento__isnull=False
            )
            .select_related("tipo")
            .only("id", "documento", "fecha_modificacion", "tipo__nombre")
            .order_by("-fecha_modificacion", "-id")
        )
        for documento in documentos_rendicion_final:
            documentos.append(
                {
                    "id": f"rendicion-final-{documento.id}",
                    "origen": "rendicion_final",
                    "tipo": documento.tipo.nombre if documento.tipo else "documento",
                    "nombre": documento.documento.name if documento.documento else None,
                    "fecha": self._coerce_datetime(documento.fecha_modificacion),
                    "url": self._build_absolute_url(request, documento.documento),
                    "path": self._file_path_from_field(documento.documento),
                }
            )

        documentos_rendicion_mensual = (
            comedor.rendiciones_cuentas_mensuales.prefetch_related("arvhios_adjuntos")
            .all()
            .order_by("-anio", "-mes")
        )
        for rendicion in documentos_rendicion_mensual:
            for adjunto in rendicion.arvhios_adjuntos.all():
                documentos.append(
                    {
                        "id": f"rendicion-mensual-{adjunto.id}",
                        "origen": "rendicion_mensual",
                        "tipo": "documento_rendicion_mensual",
                        "nombre": adjunto.archivo.name if adjunto.archivo else None,
                        "fecha": self._coerce_datetime(adjunto.ultima_modificacion),
                        "url": self._build_absolute_url(request, adjunto.archivo),
                        "path": self._file_path_from_field(adjunto.archivo),
                    }
                )

        return documentos

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="tipo",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filtrar por tipo de documento.",
            ),
            OpenApiParameter(
                name="q",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Buscar por nombre del archivo.",
            ),
            OpenApiParameter(
                name="desde",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Fecha desde (YYYY-MM-DD).",
            ),
            OpenApiParameter(
                name="hasta",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Fecha hasta (YYYY-MM-DD).",
            ),
            OpenApiParameter(
                name="page",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Página (paginación).",
            ),
        ],
        responses=DocumentoComedorSerializer(many=True),
        tags=["Comedores"],
    )
    @action(detail=True, methods=["get"], url_path="documentos")
    def documentos(self, request, pk=None):
        comedor = self.get_object()
        documentos = self._collect_documentos(comedor, request)

        filtro_tipo = (request.query_params.get("tipo") or "").strip().lower()
        if filtro_tipo:
            documentos = [
                doc
                for doc in documentos
                if doc["tipo"] and doc["tipo"].lower() == filtro_tipo
            ]

        query = (request.query_params.get("q") or "").strip().lower()
        if query:
            documentos = [
                doc
                for doc in documentos
                if doc["nombre"] and query in doc["nombre"].lower()
            ]

        desde = request.query_params.get("desde")
        hasta = request.query_params.get("hasta")
        if desde or hasta:
            try:
                desde_dt = (
                    timezone.make_aware(
                        timezone.datetime.strptime(desde, "%Y-%m-%d")
                    )
                    if desde
                    else None
                )
                hasta_dt = (
                    timezone.make_aware(
                        timezone.datetime.strptime(hasta, "%Y-%m-%d")
                    )
                    if hasta
                    else None
                )
            except (ValueError, TypeError):
                return Response(
                    {"detail": "Formato de fecha inválido."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            def _within_range(doc):
                fecha = doc.get("fecha")
                if not fecha:
                    return False
                fecha = self._coerce_datetime(fecha)
                if desde_dt and fecha < desde_dt:
                    return False
                if hasta_dt and fecha > hasta_dt:
                    return False
                return True

            documentos = [doc for doc in documentos if _within_range(doc)]

        documentos.sort(
            key=lambda doc: doc.get("fecha") or timezone.now(), reverse=True
        )

        paginator = Paginator(documentos, 20)
        page_number = request.query_params.get("page", 1)
        page_obj = paginator.get_page(page_number)

        return Response(
            {
                "count": paginator.count,
                "num_pages": paginator.num_pages,
                "current_page": page_obj.number,
                "results": DocumentoComedorSerializer(
                    page_obj.object_list, many=True
                ).data,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="documento_id",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
            )
        ],
        tags=["Comedores"],
    )
    @action(
        detail=True,
        methods=["get"],
        url_path=r"documentos/(?P<documento_id>[^/.]+)/download",
    )
    def descargar_documento(self, request, pk=None, documento_id=None):
        comedor = self.get_object()
        documentos = self._collect_documentos(comedor, request)
        documento = next((doc for doc in documentos if doc["id"] == documento_id), None)
        if not documento:
            raise Http404("Documento no encontrado.")
        file_path = documento.get("path")
        if not file_path:
            return Response(
                {"detail": "Documento sin archivo disponible."},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            return FileResponse(open(file_path, "rb"), as_attachment=True)
        except FileNotFoundError as exc:
            raise Http404("Archivo no encontrado.") from exc

    @extend_schema(
        request=NominaCreateSerializer,
        responses=NominaSerializer(many=True),
        tags=["Nomina"],
    )
    @action(detail=True, methods=["get", "post"], url_path="nomina")
    def nomina(self, request, pk=None):
        comedor = self.get_object()
        if request.method.lower() == "get":
            page = request.query_params.get("page", 1)
            page_obj, _, _, _, _, total, rangos = ComedorService.get_nomina_detail(
                comedor.pk, page
            )
            return Response(
                {
                    "count": total,
                    "current_page": page_obj.number,
                    "num_pages": page_obj.paginator.num_pages,
                    "rangos": rangos,
                    "results": NominaSerializer(page_obj.object_list, many=True).data,
                },
                status=status.HTTP_200_OK,
            )

        serializer = NominaCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        estado = data.get("estado")
        observaciones = data.get("observaciones")

        if estado is not None:
            nomina_form = NominaExtraForm(
                {"estado": estado, "observaciones": observaciones or ""}
            )
            if not nomina_form.is_valid():
                return Response(
                    {"detail": nomina_form.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if data.get("ciudadano_id"):
            ok, msg = ComedorService.agregar_ciudadano_a_nomina(
                comedor_id=comedor.pk,
                ciudadano_id=data["ciudadano_id"],
                user=request.user,
                estado=estado,
                observaciones=observaciones,
            )
            if not ok:
                return Response(
                    {"detail": msg},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response({"detail": msg}, status=status.HTTP_201_CREATED)

        ciudadano_payload = data.get("ciudadano") or {}
        ciudadano_form = CiudadanoFormParaNomina(ciudadano_payload)
        if not ciudadano_form.is_valid():
            return Response(
                {"detail": ciudadano_form.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ok, msg = ComedorService.crear_ciudadano_y_agregar_a_nomina(
            ciudadano_data=ciudadano_form.cleaned_data,
            comedor_id=comedor.pk,
            user=request.user,
            estado=estado,
            observaciones=observaciones,
        )
        if not ok:
            return Response(
                {"detail": msg},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"detail": msg}, status=status.HTTP_201_CREATED)

    @extend_schema(
        responses=InformeTecnicoPrestacionSerializer,
        tags=["Comedores"],
    )
    @action(detail=True, methods=["get"], url_path="prestacion-alimentaria")
    def prestacion_alimentaria(self, request, pk=None):
        comedor = self.get_object()
        informe = (
            InformeTecnico.objects.filter(
                admision__comedor=comedor,
                estado_formulario="finalizado",
            )
            .order_by("-modificado", "-id")
            .first()
        )
        if not informe:
            payload = {
                "informe_id": None,
                "admision_id": None,
                "tipo": None,
                "estado_formulario": None,
                "creado": None,
                "modificado": None,
            }
            payload.update({field: None for field in APROBADAS_FIELDS})
            return Response(
                payload,
                status=status.HTTP_200_OK,
            )
        return Response(
            InformeTecnicoPrestacionSerializer(informe).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="desde",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Fecha desde (YYYY-MM-DD o YYYY-MM).",
            ),
            OpenApiParameter(
                name="hasta",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Fecha hasta (YYYY-MM-DD o YYYY-MM).",
            ),
            OpenApiParameter(
                name="page",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Página (paginación).",
            ),
        ],
        responses=InformeTecnicoPrestacionSerializer(many=True),
        tags=["Comedores"],
    )
    @action(detail=True, methods=["get"], url_path="prestacion-alimentaria/historial")
    def prestacion_alimentaria_historial(self, request, pk=None):
        comedor = self.get_object()
        queryset = (
            InformeTecnico.objects.filter(
                admision__comedor=comedor,
                estado_formulario="finalizado",
            )
            .order_by("-modificado", "-id")
        )

        desde = request.query_params.get("desde")
        hasta = request.query_params.get("hasta")
        desde_date = self._parse_period_date(desde, is_end=False) if desde else None
        hasta_date = self._parse_period_date(hasta, is_end=True) if hasta else None

        if (desde and not desde_date) or (hasta and not hasta_date):
            return Response(
                {"detail": "Formato de fecha inválido."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if desde_date and hasta_date and desde_date > hasta_date:
            return Response(
                {"detail": "Rango de fechas inválido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if desde_date:
            queryset = queryset.filter(modificado__gte=desde_date)
        if hasta_date:
            queryset = queryset.filter(modificado__lte=hasta_date)

        paginator = Paginator(queryset, 20)
        page_number = request.query_params.get("page", 1)
        page_obj = paginator.get_page(page_number)

        return Response(
            {
                "count": paginator.count,
                "num_pages": paginator.num_pages,
                "current_page": page_obj.number,
                "results": InformeTecnicoPrestacionSerializer(
                    page_obj.object_list, many=True
                ).data,
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=["Nomina"])
class NominaViewSet(mixins.UpdateModelMixin, viewsets.GenericViewSet):
    serializer_class = NominaUpdateSerializer
    authentication_classes = []
    permission_classes = [HasAPIKey]
    queryset = Nomina.objects.select_related("ciudadano", "ciudadano__sexo", "comedor")
    http_method_names = ["patch", "head", "options"]

    @extend_schema(request=NominaUpdateSerializer)
    def partial_update(self, request, *args, **kwargs):
        nomina = self.get_object()
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if "estado" in data:
            nomina.estado = data["estado"]
        if "observaciones" in data:
            nomina.observaciones = data["observaciones"]
        nomina.save(update_fields=["estado", "observaciones"])
        return Response(
            NominaSerializer(nomina).data,
            status=status.HTTP_200_OK,
        )
