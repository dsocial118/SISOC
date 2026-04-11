from django.db.models import Count, Prefetch, Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.api_auth import HasAPIKeyOrToken
from VAT.models import Centro, ComisionCurso, Inscripcion, TituloReferencia, VoucherParametria
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
        OpenApiParameter(
            "q",
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            description="Busca por nombre o código.",
        ),
        OpenApiParameter(
            "provincia_id",
            OpenApiTypes.INT,
            OpenApiParameter.QUERY,
            description="Filtra por provincia.",
        ),
        OpenApiParameter(
            "municipio_id",
            OpenApiTypes.INT,
            OpenApiParameter.QUERY,
            description="Filtra por municipio.",
        ),
        OpenApiParameter(
            "localidad_id",
            OpenApiTypes.INT,
            OpenApiParameter.QUERY,
            description="Filtra por localidad.",
        ),
        OpenApiParameter(
            "activo",
            OpenApiTypes.BOOL,
            OpenApiParameter.QUERY,
            description="Por defecto devuelve solo activos.",
        ),
    ],
)
class VatWebCentroViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = VatWebCentroSerializer
    permission_classes = [HasAPIKeyOrToken]

    @extend_schema(
        summary="Listar centros VAT Web",
        responses=VatWebCentroSerializer(many=True),
        examples=[
            OpenApiExample(
                "Listado de centros",
                value=[
                    {
                        "id": 10,
                        "nombre": "CFP 777",
                        "codigo": "CFP-777",
                        "activo": True,
                        "provincia": 2,
                        "provincia_nombre": "Buenos Aires",
                        "municipio": 15,
                        "municipio_nombre": "La Plata",
                        "localidad": 120,
                        "localidad_nombre": "Tolosa",
                        "domicilio_actividad": "Calle 1 Nro 123",
                        "telefono": "221-4000000",
                        "correo": "cfp777@example.org",
                    }
                ],
                response_only=True,
            )
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

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
        OpenApiParameter(
            "q",
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            description="Busca por nombre o código de referencia.",
        ),
        OpenApiParameter(
            "sector_id",
            OpenApiTypes.INT,
            OpenApiParameter.QUERY,
            description="Filtra por sector.",
        ),
        OpenApiParameter(
            "subsector_id",
            OpenApiTypes.INT,
            OpenApiParameter.QUERY,
            description="Filtra por subsector.",
        ),
        OpenApiParameter(
            "activo",
            OpenApiTypes.BOOL,
            OpenApiParameter.QUERY,
            description="Por defecto devuelve solo activos.",
        ),
    ],
)
class VatWebTituloViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = VatWebTituloSerializer
    permission_classes = [HasAPIKeyOrToken]

    @extend_schema(
        summary="Listar títulos VAT Web",
        responses=VatWebTituloSerializer(many=True),
        examples=[
            OpenApiExample(
                "Listado de títulos",
                value=[
                    {
                        "id": 52,
                        "nombre": "Operador en Soldadura",
                        "codigo_referencia": "SOL-001",
                        "descripcion": "Trayecto inicial de soldadura",
                        "activo": True,
                        "plan_estudio": 14,
                        "sector": 3,
                        "sector_nombre": "Industria",
                        "subsector": 11,
                        "subsector_nombre": "Metalmecánica",
                    }
                ],
                response_only=True,
            )
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        queryset = TituloReferencia.objects.select_related(
            "plan_estudio", "plan_estudio__sector", "plan_estudio__subsector"
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
            queryset = queryset.filter(plan_estudio__sector_id=sector_id)
        if subsector_id:
            queryset = queryset.filter(plan_estudio__subsector_id=subsector_id)

        return queryset


@extend_schema(
    tags=["VAT Web - Cursos"],
    description="Cursos/comisiones disponibles para la web, con centro, título, programa, costo y cupos.",
    parameters=[
        OpenApiParameter(
            "q",
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            description="Busca por comisión, título o centro.",
        ),
        OpenApiParameter(
            "centro_id",
            OpenApiTypes.INT,
            OpenApiParameter.QUERY,
            description="Filtra por centro.",
        ),
        OpenApiParameter(
            "titulo_id",
            OpenApiTypes.INT,
            OpenApiParameter.QUERY,
            description="Filtra por título de referencia.",
        ),
        OpenApiParameter(
            "programa_id",
            OpenApiTypes.INT,
            OpenApiParameter.QUERY,
            description="Filtra por programa.",
        ),
        OpenApiParameter(
            "ciclo_lectivo",
            OpenApiTypes.INT,
            OpenApiParameter.QUERY,
            description="Filtra por ciclo lectivo.",
        ),
        OpenApiParameter(
            "estado",
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            description="Filtra por estado de comisión.",
        ),
        OpenApiParameter(
            "usa_voucher",
            OpenApiTypes.BOOL,
            OpenApiParameter.QUERY,
            description="Filtra por cursos que usan voucher.",
        ),
    ],
)
class VatWebCursoViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = VatWebCursoSerializer
    permission_classes = [HasAPIKeyOrToken]

    @extend_schema(
        summary="Listar cursos VAT Web",
        responses=VatWebCursoSerializer(many=True),
        examples=[
            OpenApiExample(
                "Listado de cursos",
                value=[
                    {
                        "id": 3,
                        "codigo_comision": "CUR-2026-03",
                        "nombre": "Soldadura Inicial - Comisión A",
                        "estado": "activa",
                        "estado_oferta": "activo",
                        "estado_curso": "activo",
                        "fecha_inicio": "2026-04-10",
                        "fecha_fin": "2026-08-30",
                        "cupo": 30,
                        "total_inscriptos": 12,
                        "cupos_disponibles": 18,
                        "centro_id": 10,
                        "centro_nombre": "CFP 777",
                        "titulo_id": 52,
                        "titulo_nombre": "Operador en Soldadura",
                        "plan_curricular_id": 14,
                        "plan_curricular_nombre": "Plan Soldadura 2026",
                        "programa_id": 6,
                        "programa_nombre": "Formación Laboral",
                        "ciclo_lectivo": 2026,
                        "costo": 1,
                        "usa_voucher": True,
                        "observaciones": "Comisión presencial turno tarde",
                        "horarios": [
                            {
                                "id": 101,
                                "dia_semana": 2,
                                "dia_nombre": "Martes",
                                "hora_desde": "18:00:00",
                                "hora_hasta": "21:00:00",
                                "aula_espacio": "Taller 1",
                            }
                        ],
                    }
                ],
                response_only=True,
            )
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        queryset = (
            ComisionCurso.objects.select_related(
                "curso",
                "curso__centro",
                "curso__plan_estudio",
            )
            .prefetch_related(
                "horarios__dia_semana",
                "curso__plan_estudio__titulos",
                Prefetch(
                    "curso__voucher_parametrias",
                    queryset=VoucherParametria.objects.select_related("programa").order_by(
                        "programa_id", "id"
                    ),
                ),
            )
            .annotate(total_inscriptos=Count("inscripciones", distinct=True))
            .exclude(estado__in=["cerrada", "suspendida"])
            .exclude(curso__estado__in=["finalizado", "cancelado"])
            .order_by("fecha_inicio", "codigo_comision")
        )

        q = (self.request.query_params.get("q") or "").strip()
        if q:
            queryset = queryset.filter(
                Q(nombre__icontains=q)
                | Q(codigo_comision__icontains=q)
                | Q(curso__nombre__icontains=q)
                | Q(curso__centro__nombre__icontains=q)
                | Q(curso__plan_estudio__titulos__nombre__icontains=q)
            )

        centro_id = self.request.query_params.get("centro_id")
        titulo_id = self.request.query_params.get("titulo_id")
        programa_id = self.request.query_params.get("programa_id")
        ciclo_lectivo = self.request.query_params.get("ciclo_lectivo")
        estado = self.request.query_params.get("estado")
        usa_voucher = self.request.query_params.get("usa_voucher")

        if centro_id:
            queryset = queryset.filter(curso__centro_id=centro_id)
        if titulo_id:
            queryset = queryset.filter(curso__plan_estudio__titulos__id=titulo_id)
        if programa_id:
            queryset = (
                queryset.annotate(
                    programas_distintos=Count(
                        "curso__voucher_parametrias__programa_id",
                        distinct=True,
                    )
                )
                .filter(
                    curso__voucher_parametrias__programa_id=programa_id,
                    programas_distintos=1,
                )
                .distinct()
            )
        if ciclo_lectivo:
            queryset = queryset.filter(fecha_inicio__year=ciclo_lectivo)
        if estado:
            queryset = queryset.filter(estado=estado)
        if usa_voucher is not None:
            queryset = queryset.filter(curso__usa_voucher=usa_voucher.lower() == "true")

        return queryset.distinct()


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
                "comision_curso",
                "comision_curso__curso",
                "comision_curso__curso__centro",
                "comision_curso__curso__plan_estudio",
            )
            .prefetch_related(
                "comision_curso__horarios__dia_semana",
                "comision_curso__curso__plan_estudio__titulos",
                Prefetch(
                    "comision_curso__curso__voucher_parametrias",
                    queryset=VoucherParametria.objects.select_related("programa").order_by(
                        "programa_id", "id"
                    ),
                ),
            )
            .filter(comision_curso__isnull=False)
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
            OpenApiParameter(
                "ciudadano_id",
                OpenApiTypes.INT,
                OpenApiParameter.QUERY,
                description="Filtra por ciudadano.",
            ),
            OpenApiParameter(
                "documento",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                description="Filtra por documento del ciudadano.",
            ),
            OpenApiParameter(
                "estado",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                description="Filtra por estado de inscripción.",
            ),
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
                    "comision_curso_id": 3,
                    "estado": "inscripta",
                    "observaciones": "Alta desde la web",
                },
                request_only=True,
            ),
            OpenApiExample(
                "Alta por documento",
                value={
                    "documento": "30111222",
                    "comision_curso_id": 3,
                    "estado": "pre_inscripta",
                },
                request_only=True,
            ),
        ],
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            inscripcion = serializer.save()
        except ValueError as exc:
            raise ValidationError({"error": [str(exc)]}) from exc
        response_serializer = VatWebInscripcionSerializer(
            inscripcion, context={"request": request}
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
