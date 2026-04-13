# pylint: disable=too-many-lines

import calendar
from datetime import date, time

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db.models import Prefetch, Q
from django.db.models.fields.files import FieldFile
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.timezone import make_aware
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from admisiones.models.admisiones import Admision, InformeTecnico
from comedores.api_serializers import (
    APROBADAS_FIELDS,
    ComedorDetailSerializer,
    DocumentoComedorSerializer,
    InformeTecnicoPrestacionSerializer,
    NominaCreateSerializer,
    NominaSerializer,
    NominaUpdateSerializer,
    RendicionMensualCreateSerializer,
    RendicionMensualDetailSerializer,
    RendicionMensualListSerializer,
)
from comedores.forms.comedor_form import CiudadanoFormParaNomina, NominaExtraForm
from comedores.models import (
    AuditComedorPrograma,
    CapacitacionComedorCertificado,
    Comedor,
    ImagenComedor,
    Nomina,
    Observacion,
)
from comedores.services.comedor_service import ComedorService
from comedores.services.capacitaciones_certificados_service import (
    delete_certificate,
    is_alimentar_comunidad_program,
    list_capacitaciones_certificados,
    serialize_certificate,
    submit_certificate,
)
from intervenciones.models.intervenciones import Intervencion
from relevamientos.models import ClasificacionComedor, Relevamiento
from rendicioncuentasfinal.models import DocumentoRendicionFinal
from rendicioncuentasmensual.models import DocumentacionAdjunta, RendicionCuentaMensual
from rendicioncuentasmensual.services import RendicionCuentaMensualService
from users.api_permissions import (
    HasMobileRendicionPermission,
    IsPWARepresentativeForComedor,
)
from users.api_serializers import (
    OperadorCreateResponseSerializer,
    OperadorCreateSerializer,
    OperadorListSerializer,
)
from users.services_pwa import (
    create_operador_for_comedor,
    deactivate_operador,
    get_accessible_comedor_ids,
    get_access_rows,
    is_pwa_user,
    list_operadores_for_comedor,
)

MAX_COMPROBANTE_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_COMPROBANTE_CONTENT_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.ms-excel",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/jpeg",
    "image/png",
}


@extend_schema(tags=["Comedores"])
class ComedorDetailViewSet(
    mixins.RetrieveModelMixin, viewsets.GenericViewSet
):  # pylint: disable=too-many-public-methods
    serializer_class = ComedorDetailSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def _get_scoped_comedor_ids(self):
        user = self.request.user
        if is_pwa_user(user):
            return get_accessible_comedor_ids(user)
        filtered_rows = ComedorService.get_filtered_comedores(self.request, user=user)
        return [row["id"] for row in filtered_rows]

    def _get_pwa_spaces_selector_rows(self, user):
        access_rows = list(
            get_access_rows(user).select_related(
                "comedor__provincia",
                "comedor__localidad",
                "comedor__organizacion",
                "comedor__programa",
                "comedor__ultimo_estado__estado_general__estado_actividad",
                "comedor__ultimo_estado__estado_general__estado_proceso",
            )
        )
        comedor_ids = [row.comedor_id for row in access_rows]
        access_by_comedor_id = {row.comedor_id: row for row in access_rows}

        queryset = (
            Comedor.objects.filter(id__in=comedor_ids)
            .select_related(
                "provincia",
                "localidad",
                "organizacion",
                "programa",
                "ultimo_estado__estado_general__estado_actividad",
                "ultimo_estado__estado_general__estado_proceso",
            )
            .order_by("nombre", "id")
        )

        rows = []
        for comedor in queryset:
            access = access_by_comedor_id.get(comedor.id)
            ultimo_estado = getattr(comedor, "ultimo_estado", None)
            estado_general = getattr(ultimo_estado, "estado_general", None)
            estado_actividad = getattr(
                getattr(estado_general, "estado_actividad", None), "estado", None
            )
            estado_proceso = getattr(
                getattr(estado_general, "estado_proceso", None), "estado", None
            )
            rows.append(
                {
                    "id": comedor.id,
                    "nombre": comedor.nombre,
                    "organizacion_id": comedor.organizacion_id,
                    "organizacion__nombre": (
                        comedor.organizacion.nombre if comedor.organizacion_id else None
                    ),
                    "programa_id": comedor.programa_id,
                    "programa__nombre": (
                        comedor.programa.nombre if comedor.programa_id else None
                    ),
                    "codigo_de_proyecto": comedor.codigo_de_proyecto,
                    "provincia__nombre": (
                        comedor.provincia.nombre if comedor.provincia_id else None
                    ),
                    "localidad__nombre": (
                        comedor.localidad.nombre if comedor.localidad_id else None
                    ),
                    "ultimo_estado__estado_general__estado_actividad__estado": (
                        estado_actividad
                    ),
                    "ultimo_estado__estado_general__estado_proceso__estado": (
                        estado_proceso
                    ),
                    "tipo_asociacion": (
                        getattr(access, "tipo_asociacion", None) if access else None
                    ),
                }
            )
        return rows

    def list(self, request, *args, **kwargs):
        user = request.user
        if is_pwa_user(user):
            rows = self._get_pwa_spaces_selector_rows(user)
            page = self.paginate_queryset(rows)
            if page is not None:
                return self.get_paginated_response(page)
            return Response(rows, status=status.HTTP_200_OK)
        else:
            queryset = ComedorService.get_filtered_comedores(request, user=user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            return self.get_paginated_response(page)
        return Response(list(queryset), status=status.HTTP_200_OK)

    # Los métodos de documentos se definen más abajo con su implementación real.

    def get_queryset(self):
        scoped_ids = self._get_scoped_comedor_ids()
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
                    queryset=Relevamiento.objects.select_related(
                        "comedor",
                        "comedor__referente",
                        "prestacion",
                        "funcionamiento",
                        "funcionamiento__modalidad_prestacion",
                        "espacio",
                        "espacio__tipo_espacio_fisico",
                        "espacio__cocina",
                        "espacio__cocina__abastecimiento_agua",
                        "espacio__prestacion",
                        "espacio__prestacion__desague_hinodoro",
                        "espacio__prestacion__frecuencia_limpieza",
                        "colaboradores",
                        "colaboradores__cantidad_colaboradores",
                        "recursos",
                        "compras",
                        "punto_entregas",
                        "punto_entregas__tipo_comedor",
                        "punto_entregas__frecuencia_entrega_bolsones",
                        "punto_entregas__tipo_modulo_bolsones",
                        "excepcion",
                        "excepcion__motivo",
                        "responsable_relevamiento",
                        "anexo",
                        "anexo__tecnologia",
                        "anexo__distancia_transporte",
                    )
                    .prefetch_related(
                        "espacio__cocina__abastecimiento_combustible",
                        "recursos__recursos_donaciones_particulares",
                        "recursos__recursos_estado_nacional",
                        "recursos__recursos_estado_provincial",
                        "recursos__recursos_estado_municipal",
                        "recursos__recursos_otros",
                        "punto_entregas__frecuencia_recepcion_mercaderias",
                    )
                    .order_by("-fecha_visita", "-id"),
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
                    queryset=ClasificacionComedor.objects.select_related("categoria")
                    .only(
                        "id",
                        "puntuacion_total",
                        "fecha",
                        "categoria__nombre",
                        "relevamiento",
                    )
                    .order_by("-fecha")[:3],
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
            .filter(id__in=scoped_ids)
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

        imagenes = (
            getattr(comedor, "imagenes_optimized", None) or comedor.imagenes.all()
        )
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
            comedor.rendiciones_cuentas_mensuales.prefetch_related("archivos_adjuntos")
            .all()
            .order_by("-anio", "-mes")
        )
        for rendicion in documentos_rendicion_mensual:
            for adjunto in rendicion.archivos_adjuntos.all():
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

    @action(
        detail=True,
        methods=["post"],
        url_path="imagenes",
        parser_classes=[MultiPartParser, FormParser],
    )
    def upload_imagen(self, request, pk=None):
        comedor = self.get_object()
        imagen = request.FILES.get("imagen")

        if not imagen:
            return Response(
                {"detail": "Debe adjuntar una imagen."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if comedor.imagenes.count() >= 3:
            return Response(
                {"detail": "El espacio ya tiene el máximo de 3 fotos."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        creado = ComedorService.create_imagenes(imagen, comedor.pk)
        if isinstance(creado, dict):
            return Response(creado, status=status.HTTP_400_BAD_REQUEST)

        comedor_actualizado = self.get_queryset().get(pk=comedor.pk)
        serializer = self.get_serializer(comedor_actualizado)
        return Response(
            {"imagenes": serializer.data.get("imagenes", [])},
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path=r"imagenes/(?P<imagen_id>[^/.]+)/eliminar",
    )
    def eliminar_imagen(self, request, pk=None, imagen_id=None):
        comedor = self.get_object()
        imagen = get_object_or_404(ImagenComedor, pk=imagen_id, comedor=comedor)
        imagen.delete()

        comedor_actualizado = self.get_queryset().get(pk=comedor.pk)
        serializer = self.get_serializer(comedor_actualizado)
        return Response(
            {"imagenes": serializer.data.get("imagenes", [])},
            status=status.HTTP_200_OK,
        )

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
                    timezone.make_aware(timezone.datetime.strptime(desde, "%Y-%m-%d"))
                    if desde
                    else None
                )
                hasta_dt = (
                    timezone.make_aware(
                        timezone.datetime.combine(
                            timezone.datetime.strptime(hasta, "%Y-%m-%d").date(),
                            time.max,
                        )
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

    def _nomina_get(self, request, admision):
        page = request.query_params.get("page", 1)
        page_obj, _, _, _, _, total, rangos = ComedorService.get_nomina_detail(
            admision.pk, page
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

    def _nomina_post(self, request, admision):
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
                admision_id=admision.pk,
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
            admision_id=admision.pk,
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
        request=NominaCreateSerializer,
        responses=NominaSerializer(many=True),
        tags=["Nomina"],
    )
    @action(detail=True, methods=["get", "post"], url_path="nomina")
    def nomina(self, request, pk=None):
        comedor = self.get_object()
        admision = (
            Admision.objects.filter(comedor=comedor, activa=True)
            .order_by("-id")
            .first()
            or Admision.objects.filter(comedor=comedor).order_by("-id").first()
        )
        if not admision:
            return Response(
                {"detail": "No hay admisión para este comedor."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if request.method.lower() == "get":
            return self._nomina_get(request, admision)
        return self._nomina_post(request, admision)

    def _format_validation_error(self, exc: ValidationError):
        if hasattr(exc, "message_dict"):
            return exc.message_dict
        if hasattr(exc, "messages"):
            return exc.messages
        return str(exc)

    def _validate_comprobante_file(self, archivo):
        if not archivo:
            return "Debe adjuntar un archivo."
        if archivo.content_type not in ALLOWED_COMPROBANTE_CONTENT_TYPES:
            return "Tipo de archivo no permitido. Formatos válidos: PDF, JPG, PNG."
        if archivo.size > MAX_COMPROBANTE_FILE_SIZE:
            return "El archivo excede el tamaño máximo permitido de 10 MB."
        return None

    @action(
        detail=True,
        methods=["get"],
        url_path="capacitaciones",
        permission_classes=[IsPWARepresentativeForComedor],
    )
    def capacitaciones(self, request, pk=None):
        comedor = self.get_object()
        if not is_alimentar_comunidad_program(comedor):
            return Response(
                {
                    "detail": "Capacitaciones disponibles solo para programa Alimentar Comunidad."
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        records = list_capacitaciones_certificados(comedor)
        return Response(
            [serialize_certificate(record, request=request) for record in records],
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="capacitaciones/subir",
        parser_classes=[MultiPartParser, FormParser],
        permission_classes=[IsPWARepresentativeForComedor],
    )
    def subir_capacitacion(self, request, pk=None):
        comedor = self.get_object()
        if not is_alimentar_comunidad_program(comedor):
            return Response(
                {
                    "detail": "Capacitaciones disponibles solo para programa Alimentar Comunidad."
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        capacitacion = (request.data.get("capacitacion") or "").strip()
        archivo = request.FILES.get("archivo")

        if capacitacion not in dict(
            CapacitacionComedorCertificado.CAPACITACION_CHOICES
        ):
            return Response(
                {"detail": "Capacitación inválida."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        record = CapacitacionComedorCertificado.objects.filter(
            comedor=comedor,
            capacitacion=capacitacion,
        ).first()
        if not record:
            records = list_capacitaciones_certificados(comedor)
            record = next(
                (row for row in records if row.capacitacion == capacitacion), None
            )

        try:
            submit_certificate(record, archivo, request.user)
        except ValidationError as exc:
            return Response(
                {"detail": self._format_validation_error(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            serialize_certificate(record, request=request),
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="capacitaciones/eliminar",
    )
    def eliminar_capacitacion(self, request, pk=None):
        comedor = self.get_object()
        if not is_alimentar_comunidad_program(comedor):
            return Response(
                {
                    "detail": "La sección de capacitaciones aplica solo a Alimentar Comunidad."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        capacitacion = (request.data.get("capacitacion") or "").strip()
        if capacitacion not in dict(
            CapacitacionComedorCertificado.CAPACITACION_CHOICES
        ):
            return Response(
                {"detail": "Capacitación inválida."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            records = list_capacitaciones_certificados(comedor)
            record = next(
                (row for row in records if row.capacitacion == capacitacion), None
            )
            if not record:
                return Response(
                    {"detail": "No se encontró la capacitación."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            delete_certificate(record)
        except ValidationError as exc:
            message = exc.messages[0] if getattr(exc, "messages", None) else str(exc)
            return Response({"detail": message}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            serialize_certificate(record, request=request),
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        request=OperadorCreateSerializer,
        responses=OperadorListSerializer(many=True),
        tags=["Comedores"],
    )
    @action(
        detail=True,
        methods=["get", "post"],
        url_path="usuarios",
        permission_classes=[IsPWARepresentativeForComedor],
    )
    def usuarios(self, request, pk=None):
        comedor = self.get_object()
        if request.method.lower() == "get":
            queryset = list_operadores_for_comedor(comedor.id)
            paginator = Paginator(queryset, 20)
            page_number = request.query_params.get("page", 1)
            page_obj = paginator.get_page(page_number)
            return Response(
                {
                    "count": paginator.count,
                    "num_pages": paginator.num_pages,
                    "current_page": page_obj.number,
                    "results": OperadorListSerializer(
                        page_obj.object_list, many=True
                    ).data,
                },
                status=status.HTTP_200_OK,
            )

        serializer = OperadorCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            acceso = create_operador_for_comedor(
                comedor_id=comedor.id,
                actor=request.user,
                username=serializer.validated_data["username"],
                email=serializer.validated_data["email"],
                password=serializer.validated_data["password"],
            )
        except PermissionDenied as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_403_FORBIDDEN,
            )
        except ValidationError as exc:
            return Response(
                {"detail": self._format_validation_error(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            OperadorCreateResponseSerializer(acceso).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        request=None,
        tags=["Comedores"],
    )
    @action(
        detail=True,
        methods=["patch"],
        url_path=r"usuarios/(?P<user_id>[^/.]+)/desactivar",
        permission_classes=[IsPWARepresentativeForComedor],
    )
    def desactivar_usuario(self, request, pk=None, user_id=None):
        comedor = self.get_object()
        try:
            deactivate_operador(
                comedor_id=comedor.id,
                user_id=int(user_id),
                actor=request.user,
            )
        except ValueError:
            return Response(
                {"detail": "user_id inválido."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except PermissionDenied as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_403_FORBIDDEN,
            )
        except ValidationError as exc:
            return Response(
                {"detail": self._format_validation_error(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"detail": "Usuario desactivado."},
            status=status.HTTP_200_OK,
        )

    def _get_rendiciones_queryset(self, comedor):
        return (
            RendicionCuentaMensualService.obtener_rendiciones_cuentas_mensuales(comedor)
            .only(
                "id",
                "convenio",
                "numero_rendicion",
                "mes",
                "anio",
                "periodo_inicio",
                "periodo_fin",
                "estado",
                "documento_adjunto",
                "observaciones",
                "fecha_creacion",
                "ultima_modificacion",
            )
            .order_by("-fecha_creacion", "-id")
        )

    def _get_rendiciones_detail_queryset(self, comedor):
        return (
            RendicionCuentaMensualService.obtener_rendiciones_cuentas_mensuales(comedor)
            .prefetch_related("archivos_adjuntos")
            .order_by("-fecha_creacion", "-id")
        )

    def _apply_periodo_filters_rendiciones(self, queryset, request):
        anio = request.query_params.get("anio")
        mes = request.query_params.get("mes")

        if anio:
            try:
                queryset = queryset.filter(anio=int(anio))
            except (TypeError, ValueError) as exc:
                raise ValidationError("Parámetro anio inválido.") from exc

        if mes:
            try:
                mes_int = int(mes)
            except (TypeError, ValueError) as exc:
                raise ValidationError("Parámetro mes inválido.") from exc
            if mes_int < 1 or mes_int > 12:
                raise ValidationError("Parámetro mes inválido.")
            queryset = queryset.filter(mes=mes_int)

        desde = request.query_params.get("desde")
        hasta = request.query_params.get("hasta")
        if not desde and not hasta:
            return queryset

        desde_date = self._parse_period_date(desde, is_end=False) if desde else None
        hasta_date = self._parse_period_date(hasta, is_end=True) if hasta else None

        if (desde and not desde_date) or (hasta and not hasta_date):
            raise ValidationError("Formato de período inválido.")
        if desde_date and hasta_date and desde_date > hasta_date:
            raise ValidationError("Rango de períodos inválido.")

        if desde_date:
            queryset = queryset.filter(
                Q(anio__gt=desde_date.year)
                | (Q(anio=desde_date.year) & Q(mes__gte=desde_date.month))
            )
        if hasta_date:
            queryset = queryset.filter(
                Q(anio__lt=hasta_date.year)
                | (Q(anio=hasta_date.year) & Q(mes__lte=hasta_date.month))
            )
        return queryset

    @extend_schema(
        request=RendicionMensualCreateSerializer,
        responses=RendicionMensualListSerializer(many=True),
        tags=["Rendiciones"],
    )
    @action(
        detail=True,
        methods=["get", "post"],
        url_path="rendiciones",
        permission_classes=[
            IsPWARepresentativeForComedor,
            HasMobileRendicionPermission,
        ],
    )
    def rendiciones(self, request, pk=None):
        comedor = self.get_object()
        if request.method.lower() == "post":
            serializer = RendicionMensualCreateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            try:
                rendicion = RendicionCuentaMensualService.crear_rendicion_mobile(
                    comedor=comedor,
                    data=serializer.validated_data,
                    actor=request.user,
                )
            except ValidationError as exc:
                return Response(
                    {"detail": self._format_validation_error(exc)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                RendicionMensualDetailSerializer(
                    rendicion,
                    context={"request": request},
                ).data,
                status=status.HTTP_201_CREATED,
            )

        queryset = self._get_rendiciones_queryset(comedor)
        try:
            queryset = self._apply_periodo_filters_rendiciones(queryset, request)
        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        paginator = Paginator(queryset, 20)
        page_number = request.query_params.get("page", 1)
        page_obj = paginator.get_page(page_number)

        serializer = RendicionMensualListSerializer(
            page_obj.object_list,
            many=True,
        )
        return Response(
            {
                "count": paginator.count,
                "num_pages": paginator.num_pages,
                "current_page": page_obj.number,
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        responses=RendicionMensualDetailSerializer,
        tags=["Rendiciones"],
    )
    @action(
        detail=True,
        methods=["get"],
        url_path=r"rendiciones/(?P<rendicion_id>[^/.]+)",
        permission_classes=[
            IsPWARepresentativeForComedor,
            HasMobileRendicionPermission,
        ],
    )
    def rendicion_detalle(self, request, pk=None, rendicion_id=None):
        comedor = self.get_object()
        try:
            rendicion_id = int(rendicion_id)
        except (TypeError, ValueError):
            return Response(
                {"detail": "rendicion_id inválido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        rendicion = (
            self._get_rendiciones_detail_queryset(comedor)
            .filter(id=rendicion_id)
            .first()
        )
        if not rendicion:
            raise Http404("Rendición no encontrada.")

        serializer = RendicionMensualDetailSerializer(
            rendicion,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=None,
        responses=RendicionMensualDetailSerializer,
        tags=["Rendiciones"],
    )
    @action(
        detail=True,
        methods=["post"],
        url_path=r"rendiciones/(?P<rendicion_id>[^/.]+)/documentacion",
        parser_classes=[MultiPartParser, FormParser],
        permission_classes=[
            IsPWARepresentativeForComedor,
            HasMobileRendicionPermission,
        ],
    )
    def adjuntar_documentacion_rendicion(self, request, pk=None, rendicion_id=None):
        comedor = self.get_object()
        try:
            rendicion_id = int(rendicion_id)
        except (TypeError, ValueError):
            return Response(
                {"detail": "rendicion_id inválido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        rendicion = (
            self._get_rendiciones_detail_queryset(comedor)
            .filter(id=rendicion_id)
            .first()
        )
        if not rendicion:
            raise Http404("Rendición no encontrada.")

        return self._adjuntar_documentacion_respuesta(
            request,
            comedor=comedor,
            rendicion=rendicion,
        )

    def _adjuntar_documentacion_respuesta(
        self,
        request,
        *,
        comedor,
        rendicion,
        categoria_override=None,
    ):

        archivo = request.FILES.get("archivo")
        file_error = self._validate_comprobante_file(archivo)
        if file_error:
            return Response(
                {"detail": file_error},
                status=status.HTTP_400_BAD_REQUEST,
            )

        categoria = categoria_override or (request.data.get("categoria") or "").strip()
        nombre = (request.data.get("nombre") or "").strip() or archivo.name
        documento_subsanado_id = request.data.get("documento_subsanado_id")
        if documento_subsanado_id not in (None, ""):
            try:
                documento_subsanado_id = int(documento_subsanado_id)
            except (TypeError, ValueError):
                return Response(
                    {"detail": "documento_subsanado_id inválido."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        try:
            RendicionCuentaMensualService.adjuntar_documentacion_mobile(
                rendicion=rendicion,
                categoria=categoria,
                documento_data={"archivo": archivo, "nombre": nombre},
                actor=request.user,
                documento_subsanado_id=documento_subsanado_id,
            )
        except ValidationError as exc:
            return Response(
                {"detail": self._format_validation_error(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = RendicionMensualDetailSerializer(
            self._get_rendiciones_detail_queryset(comedor).get(id=rendicion.id),
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        request=None,
        responses=RendicionMensualDetailSerializer,
        tags=["Rendiciones"],
    )
    @action(
        detail=True,
        methods=["post"],
        url_path=r"rendiciones/(?P<rendicion_id>[^/.]+)/documentacion/(?P<documento_id>[^/.]+)/eliminar",
        permission_classes=[
            IsPWARepresentativeForComedor,
            HasMobileRendicionPermission,
        ],
    )
    def eliminar_documentacion_rendicion(
        self, request, pk=None, rendicion_id=None, documento_id=None
    ):
        comedor = self.get_object()
        try:
            rendicion_id = int(rendicion_id)
            documento_id = int(documento_id)
        except (TypeError, ValueError):
            return Response(
                {"detail": "documento_id inválido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        rendicion = (
            self._get_rendiciones_detail_queryset(comedor)
            .filter(id=rendicion_id)
            .first()
        )
        if not rendicion:
            raise Http404("Rendición no encontrada.")

        documento = rendicion.archivos_adjuntos.filter(
            id=documento_id,
            deleted_at__isnull=True,
        ).first()
        if not documento:
            raise Http404("Documento no encontrado.")

        try:
            RendicionCuentaMensualService.eliminar_documentacion_mobile(
                rendicion=rendicion,
                documento=documento,
                actor=request.user,
            )
        except ValidationError as exc:
            return Response(
                {"detail": self._format_validation_error(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = RendicionMensualDetailSerializer(
            self._get_rendiciones_detail_queryset(comedor).get(id=rendicion.id),
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=None,
        responses=RendicionMensualDetailSerializer,
        tags=["Rendiciones"],
    )
    @action(
        detail=True,
        methods=["post"],
        url_path=r"rendiciones/(?P<rendicion_id>[^/.]+)/comprobantes",
        parser_classes=[MultiPartParser, FormParser],
        permission_classes=[
            IsPWARepresentativeForComedor,
            HasMobileRendicionPermission,
        ],
    )
    def adjuntar_comprobante_rendicion(self, request, pk=None, rendicion_id=None):
        comedor = self.get_object()
        try:
            rendicion_id = int(rendicion_id)
        except (TypeError, ValueError):
            return Response(
                {"detail": "rendicion_id inválido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        rendicion = (
            self._get_rendiciones_detail_queryset(comedor)
            .filter(id=rendicion_id)
            .first()
        )
        if not rendicion:
            raise Http404("Rendición no encontrada.")

        return self._adjuntar_documentacion_respuesta(
            request,
            comedor=comedor,
            rendicion=rendicion,
            categoria_override=DocumentacionAdjunta.CATEGORIA_COMPROBANTES,
        )

    @extend_schema(
        request=None,
        tags=["Rendiciones"],
    )
    @action(
        detail=True,
        methods=["post"],
        url_path=r"rendiciones/(?P<rendicion_id>[^/.]+)/presentar",
        permission_classes=[
            IsPWARepresentativeForComedor,
            HasMobileRendicionPermission,
        ],
    )
    def presentar_rendicion(self, request, pk=None, rendicion_id=None):
        comedor = self.get_object()
        try:
            rendicion_id = int(rendicion_id)
        except (TypeError, ValueError):
            return Response(
                {"detail": "rendicion_id inválido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        rendicion = (
            self._get_rendiciones_detail_queryset(comedor)
            .filter(id=rendicion_id)
            .first()
        )
        if not rendicion:
            raise Http404("Rendición no encontrada.")

        try:
            RendicionCuentaMensualService.presentar_rendicion_mobile(
                rendicion,
                actor=request.user,
            )
        except ValidationError as exc:
            return Response(
                {"detail": self._format_validation_error(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"detail": "Rendición presentada."},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        request=None,
        tags=["Rendiciones"],
    )
    @action(
        detail=True,
        methods=["post"],
        url_path=r"rendiciones/(?P<rendicion_id>[^/.]+)/eliminar",
        permission_classes=[
            IsPWARepresentativeForComedor,
            HasMobileRendicionPermission,
        ],
    )
    def eliminar_rendicion(self, request, pk=None, rendicion_id=None):
        comedor = self.get_object()
        try:
            rendicion_id = int(rendicion_id)
        except (TypeError, ValueError):
            return Response(
                {"detail": "rendicion_id inválido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        rendicion = (
            self._get_rendiciones_detail_queryset(comedor)
            .filter(id=rendicion_id)
            .first()
        )
        if not rendicion:
            raise Http404("Rendición no encontrada.")

        try:
            RendicionCuentaMensualService.eliminar_rendicion_mobile(rendicion)
        except ValidationError as exc:
            return Response(
                {"detail": self._format_validation_error(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"detail": "Rendición eliminada."},
            status=status.HTTP_200_OK,
        )

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
        queryset = InformeTecnico.objects.filter(
            admision__comedor=comedor,
            estado_formulario="finalizado",
        ).order_by("-modificado", "-id")

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
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Nomina.objects.select_related(
        "ciudadano", "ciudadano__sexo", "admision__comedor"
    )
    http_method_names = ["patch", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        if is_pwa_user(user):
            comedor_ids = get_accessible_comedor_ids(user)
        else:
            filtered_rows = ComedorService.get_filtered_comedores(
                self.request, user=user
            )
            comedor_ids = [row["id"] for row in filtered_rows]
        return self.queryset.filter(admision__comedor_id__in=comedor_ids)

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
