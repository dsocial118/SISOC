from django.db.models import Count, Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.response import Response

from core.api_auth import HasAPIKeyOrToken
from VAT.models import Centro, Comision, Inscripcion, TituloReferencia
from VAT.serializers import (
    VatWebCentroSerializer,
    VatWebCursoSerializer,
    VatWebInscripcionCreateSerializer,
    VatWebInscripcionSerializer,
    VatWebTituloSerializer,
)


@extend_schema(
    tags=["VAT Web - Centros"],
    description="Centros visibles para la web. Permite búsqueda textual y filtros geográficos.",
    parameters=[
        OpenApiParameter("q", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Busca por nombre o código."),
        OpenApiParameter("provincia_id", OpenApiTypes.INT, OpenApiParameter.QUERY, description="Filtra por provincia."),
        OpenApiParameter("municipio_id", OpenApiTypes.INT, OpenApiParameter.QUERY, description="Filtra por municipio."),
        OpenApiParameter("localidad_id", OpenApiTypes.INT, OpenApiParameter.QUERY, description="Filtra por localidad."),
        OpenApiParameter("activo", OpenApiTypes.BOOL, OpenApiParameter.QUERY, description="Por defecto devuelve solo activos."),
    ],
)
class VatWebCentroViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = VatWebCentroSerializer
    permission_classes = [HasAPIKeyOrToken]

    def get_queryset(self):
        queryset = Centro.objects.select_related(
            "provincia", "municipio", "localidad"
        ).order_by("nombre")

        activo = self.request.query_params.get("activo")
        if activo is None:
            queryset = queryset.filter(activo=True)
        else:
            queryset = queryset.filter(activo=activo.lower() == "true")

        q = (self.request.query_params.get("q") or "").strip()
        if q:
            queryset = queryset.filter(Q(nombre__icontains=q) | Q(codigo__icontains=q))

        provincia_id = self.request.query_params.get("provincia_id")
        municipio_id = self.request.query_params.get("municipio_id")
        localidad_id = self.request.query_params.get("localidad_id")
        if provincia_id:
            queryset = queryset.filter(provincia_id=provincia_id)
        if municipio_id:
            queryset = queryset.filter(municipio_id=municipio_id)
        if localidad_id:
            queryset = queryset.filter(localidad_id=localidad_id)

        return queryset


@extend_schema(
    tags=["VAT Web - Títulos"],
    description="Títulos de referencia disponibles para navegación web.",
    parameters=[
        OpenApiParameter("q", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Busca por nombre o código de referencia."),
        OpenApiParameter("sector_id", OpenApiTypes.INT, OpenApiParameter.QUERY, description="Filtra por sector."),
        OpenApiParameter("subsector_id", OpenApiTypes.INT, OpenApiParameter.QUERY, description="Filtra por subsector."),
        OpenApiParameter("activo", OpenApiTypes.BOOL, OpenApiParameter.QUERY, description="Por defecto devuelve solo activos."),
    ],
)
class VatWebTituloViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = VatWebTituloSerializer
    permission_classes = [HasAPIKeyOrToken]

    def get_queryset(self):
        queryset = TituloReferencia.objects.select_related(
            "sector", "subsector"
        ).order_by("nombre")

        activo = self.request.query_params.get("activo")
        if activo is None:
            queryset = queryset.filter(activo=True)
        else:
            queryset = queryset.filter(activo=activo.lower() == "true")

        q = (self.request.query_params.get("q") or "").strip()
        if q:
            queryset = queryset.filter(
                Q(nombre__icontains=q) | Q(codigo_referencia__icontains=q)
            )

        sector_id = self.request.query_params.get("sector_id")
        subsector_id = self.request.query_params.get("subsector_id")
        if sector_id:
            queryset = queryset.filter(sector_id=sector_id)
        if subsector_id:
            queryset = queryset.filter(subsector_id=subsector_id)

        return queryset


@extend_schema(
    tags=["VAT Web - Cursos"],
    description="Cursos/comisiones disponibles para la web, con centro, título, programa, costo y cupos.",
    parameters=[
        OpenApiParameter("q", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Busca por comisión, título o centro."),
        OpenApiParameter("centro_id", OpenApiTypes.INT, OpenApiParameter.QUERY, description="Filtra por centro."),
        OpenApiParameter("titulo_id", OpenApiTypes.INT, OpenApiParameter.QUERY, description="Filtra por título de referencia."),
        OpenApiParameter("programa_id", OpenApiTypes.INT, OpenApiParameter.QUERY, description="Filtra por programa."),
        OpenApiParameter("ciclo_lectivo", OpenApiTypes.INT, OpenApiParameter.QUERY, description="Filtra por ciclo lectivo."),
        OpenApiParameter("estado", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Filtra por estado de comisión."),
        OpenApiParameter("usa_voucher", OpenApiTypes.BOOL, OpenApiParameter.QUERY, description="Filtra por cursos que usan voucher."),
    ],
)
class VatWebCursoViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = VatWebCursoSerializer
    permission_classes = [HasAPIKeyOrToken]

    def get_queryset(self):
        queryset = (
            Comision.objects.select_related(
                "oferta__centro",
                "oferta__plan_curricular__titulo_referencia",
                "oferta__programa",
            )
            .prefetch_related("horarios__dia_semana")
            .annotate(total_inscriptos=Count("inscripciones", distinct=True))
            .exclude(estado__in=["cerrada", "suspendida"])
            .exclude(oferta__estado="cancelada")
            .order_by("fecha_inicio", "codigo_comision")
        )

        q = (self.request.query_params.get("q") or "").strip()
        if q:
            queryset = queryset.filter(
                Q(nombre__icontains=q)
                | Q(codigo_comision__icontains=q)
                | Q(oferta__centro__nombre__icontains=q)
                | Q(oferta__plan_curricular__titulo_referencia__nombre__icontains=q)
            )

        centro_id = self.request.query_params.get("centro_id")
        titulo_id = self.request.query_params.get("titulo_id")
        programa_id = self.request.query_params.get("programa_id")
        ciclo_lectivo = self.request.query_params.get("ciclo_lectivo")
        estado = self.request.query_params.get("estado")
        usa_voucher = self.request.query_params.get("usa_voucher")

        if centro_id:
            queryset = queryset.filter(oferta__centro_id=centro_id)
        if titulo_id:
            queryset = queryset.filter(
                oferta__plan_curricular__titulo_referencia_id=titulo_id
            )
        if programa_id:
            queryset = queryset.filter(oferta__programa_id=programa_id)
        if ciclo_lectivo:
            queryset = queryset.filter(oferta__ciclo_lectivo=ciclo_lectivo)
        if estado:
            queryset = queryset.filter(estado=estado)
        if usa_voucher is not None:
            queryset = queryset.filter(oferta__usa_voucher=usa_voucher.lower() == "true")

        return queryset


@extend_schema(
    tags=["VAT Web - Inscripciones"],
    description="Consulta y alta de inscripciones VAT para consumo de la web.",
)
class VatWebInscripcionViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    permission_classes = [HasAPIKeyOrToken]

    def get_queryset(self):
        queryset = (
            Inscripcion.objects.select_related(
                "ciudadano",
                "programa",
                "comision__oferta__centro",
                "comision__oferta__plan_curricular__titulo_referencia",
            )
            .prefetch_related("comision__horarios__dia_semana")
            .annotate(total_inscriptos=Count("comision__inscripciones", distinct=True))
            .order_by("-fecha_inscripcion")
        )

        ciudadano_id = self.request.query_params.get("ciudadano_id")
        documento = self.request.query_params.get("documento")
        estado = self.request.query_params.get("estado")

        if ciudadano_id:
            queryset = queryset.filter(ciudadano_id=ciudadano_id)
        if documento and str(documento).isdigit():
            queryset = queryset.filter(ciudadano__documento=int(documento))
        if estado:
            queryset = queryset.filter(estado=estado)

        return queryset

    def get_serializer_class(self):
        if self.action == "create":
            return VatWebInscripcionCreateSerializer
        return VatWebInscripcionSerializer

    @extend_schema(
        summary="Listar inscripciones VAT",
        parameters=[
            OpenApiParameter("ciudadano_id", OpenApiTypes.INT, OpenApiParameter.QUERY, description="Filtra por ciudadano."),
            OpenApiParameter("documento", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Filtra por documento del ciudadano."),
            OpenApiParameter("estado", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Filtra por estado de inscripción."),
        ],
        responses=VatWebInscripcionSerializer(many=True),
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Crear inscripción VAT",
        request=VatWebInscripcionCreateSerializer,
        responses={201: VatWebInscripcionSerializer},
        examples=[
            OpenApiExample(
                "Alta por ciudadano_id",
                value={
                    "ciudadano_id": 1,
                    "comision_id": 3,
                    "estado": "inscripta",
                    "observaciones": "Alta desde la web",
                },
                request_only=True,
            ),
            OpenApiExample(
                "Alta por documento",
                value={
                    "documento": "30111222",
                    "comision_id": 3,
                    "estado": "pre_inscripta",
                },
                request_only=True,
            ),
        ],
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        inscripcion = serializer.save()
        response_serializer = VatWebInscripcionSerializer(
            inscripcion, context={"request": request}
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
