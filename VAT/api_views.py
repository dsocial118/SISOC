import logging

from django.db.models import Count, Prefetch, Q
from drf_spectacular.utils import extend_schema
from drf_spectacular.utils import OpenApiExample, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from VAT.models import (
    Centro,
    ModalidadInstitucional,
    Sector,
    Subsector,
    TituloReferencia,
    ModalidadCursada,
    PlanVersionCurricular,
    InscripcionOferta,
    Voucher,
    InstitucionContacto,
    InstitucionIdentificadorHist,
    InstitucionUbicacion,
    Curso,
    ComisionCurso,
    VoucherParametria,
    OfertaInstitucional,
    Comision,
    ComisionHorario,
    Inscripcion,
    Evaluacion,
    ResultadoEvaluacion,
)
from VAT.serializers import (
    CentroSerializer,
    ProvinciaSerializer,
    MunicipioSerializer,
    LocalidadSerializer,
    ModalidadInstitucionalSerializer,
    SectorSerializer,
    SubsectorSerializer,
    TituloReferenciaSerializer,
    ModalidadCursadaSerializer,
    PlanVersionCurricularSerializer,
    InscripcionOfertaSerializer,
    VoucherSerializer,
    InstitucionContactoSerializer,
    InstitucionIdentificadorHistSerializer,
    InstitucionUbicacionSerializer,
    CursoSerializer,
    CursoBusquedaSerializer,
    ComisionCursoSerializer,
    OfertaInstitucionalSerializer,
    ComisionSerializer,
    ComisionHorarioSerializer,
    InscripcionSerializer,
    EvaluacionSerializer,
    ResultadoEvaluacionSerializer,
)
from VAT.services.inscripcion_service import InscripcionService
from core.api_auth import HasAPIKey
from core.models import Localidad, Municipio, Provincia
from core.soft_delete.view_helpers import is_soft_deletable_instance

logger = logging.getLogger("django")


class SoftDeleteDestroyMixin:
    def perform_destroy(self, instance):
        if is_soft_deletable_instance(instance):
            user = (
                self.request.user
                if getattr(self.request.user, "is_authenticated", False)
                else None
            )
            instance.delete(user=user, cascade=True)
            return
        super().perform_destroy(instance)


@extend_schema(tags=["VAT - Centros"])
class CentroViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    queryset = Centro.objects.select_related(
        "referente", "provincia", "municipio", "localidad"
    ).order_by("id")
    serializer_class = CentroSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        activo = self.request.query_params.get("activo")
        if activo is not None:
            queryset = queryset.filter(activo=activo.lower() == "true")
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

    @action(detail=False, methods=["get"])
    def activos(self, request):
        centros = self.get_queryset().filter(activo=True)
        serializer = self.get_serializer(centros, many=True)
        return Response(serializer.data)


@extend_schema(tags=["VAT - Ubicación"])
class ProvinciaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Provincia.objects.all().order_by("nombre")
    serializer_class = ProvinciaSerializer
    permission_classes = [HasAPIKey]


@extend_schema(tags=["VAT - Ubicación"])
class MunicipioViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Municipio.objects.select_related("provincia").order_by("nombre")
    serializer_class = MunicipioSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        provincia_id = self.request.query_params.get("provincia_id")
        if provincia_id:
            queryset = queryset.filter(provincia_id=provincia_id)
        return queryset


@extend_schema(tags=["VAT - Ubicación"])
class LocalidadViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Localidad.objects.select_related("municipio__provincia").order_by(
        "nombre"
    )
    serializer_class = LocalidadSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        municipio_id = self.request.query_params.get("municipio_id")
        provincia_id = self.request.query_params.get("provincia_id")
        if municipio_id:
            queryset = queryset.filter(municipio_id=municipio_id)
        elif provincia_id:
            queryset = queryset.filter(municipio__provincia_id=provincia_id)
        return queryset


@extend_schema(tags=["VAT - Modalidades Institucionales"])
class ModalidadInstitucionalViewSet(viewsets.ModelViewSet):
    queryset = ModalidadInstitucional.objects.all().order_by("nombre")
    serializer_class = ModalidadInstitucionalSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        activo = self.request.query_params.get("activo")
        if activo is not None:
            queryset = queryset.filter(activo=activo.lower() == "true")
        return queryset


@extend_schema(tags=["VAT - Catálogos Académicos"])
class SectorViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    queryset = Sector.objects.all().order_by("nombre")
    serializer_class = SectorSerializer
    permission_classes = [HasAPIKey]


@extend_schema(tags=["VAT - Catálogos Académicos"])
class SubsectorViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    queryset = Subsector.objects.select_related("sector").order_by("sector", "nombre")
    serializer_class = SubsectorSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        sector_id = self.request.query_params.get("sector_id")
        if sector_id:
            queryset = queryset.filter(sector_id=sector_id)
        return queryset


@extend_schema(tags=["VAT - Catálogos Académicos"])
class TituloReferenciaViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    queryset = TituloReferencia.objects.select_related(
        "plan_estudio", "plan_estudio__sector", "plan_estudio__subsector"
    ).order_by("nombre")
    serializer_class = TituloReferenciaSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        sector_id = self.request.query_params.get("sector_id")
        subsector_id = self.request.query_params.get("subsector_id")
        activo = self.request.query_params.get("activo")
        if sector_id:
            queryset = queryset.filter(plan_estudio__sector_id=sector_id)
        if subsector_id:
            queryset = queryset.filter(plan_estudio__subsector_id=subsector_id)
        if activo is not None:
            queryset = queryset.filter(activo=activo.lower() == "true")
        return queryset


@extend_schema(tags=["VAT - Catálogos Académicos"])
class ModalidadCursadaViewSet(viewsets.ModelViewSet):
    queryset = ModalidadCursada.objects.all().order_by("nombre")
    serializer_class = ModalidadCursadaSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        activo = self.request.query_params.get("activo")
        if activo is not None:
            queryset = queryset.filter(activo=activo.lower() == "true")
        return queryset


@extend_schema(tags=["VAT - Catálogos Académicos"])
class PlanVersionCurricularViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    queryset = PlanVersionCurricular.objects.select_related(
        "sector", "subsector", "modalidad_cursada"
    ).order_by("sector", "modalidad_cursada")
    serializer_class = PlanVersionCurricularSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        sector_id = self.request.query_params.get("sector_id")
        subsector_id = self.request.query_params.get("subsector_id")
        titulo_referencia_id = self.request.query_params.get("titulo_referencia_id")
        modalidad_cursada_id = self.request.query_params.get("modalidad_cursada_id")
        activo = self.request.query_params.get("activo")
        if sector_id:
            queryset = queryset.filter(sector_id=sector_id)
        if subsector_id:
            queryset = queryset.filter(subsector_id=subsector_id)
        if titulo_referencia_id:
            queryset = queryset.filter(titulos__id=titulo_referencia_id)
        if modalidad_cursada_id:
            queryset = queryset.filter(modalidad_cursada_id=modalidad_cursada_id)
        if activo is not None:
            queryset = queryset.filter(activo=activo.lower() == "true")
        return queryset


@extend_schema(tags=["VAT - Inscripciones"])
class InscripcionOfertaViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    queryset = InscripcionOferta.objects.select_related("oferta", "ciudadano").order_by(
        "-fecha_inscripcion"
    )
    serializer_class = InscripcionOfertaSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        oferta_id = self.request.query_params.get("oferta_id")
        estado = self.request.query_params.get("estado")
        if oferta_id:
            queryset = queryset.filter(oferta_id=oferta_id)
        if estado:
            queryset = queryset.filter(estado=estado)
        return queryset

    def perform_create(self, serializer):
        data = serializer.validated_data
        try:
            inscripcion = InscripcionService.crear_inscripcion_oferta(
                ciudadano=data["ciudadano"],
                comision=data["oferta"],
                estado=data.get("estado", "inscrito"),
                inscrito_por=getattr(self.request, "user", None),
            )
        except ValueError as exc:
            raise ValidationError({"error": [str(exc)]}) from exc

        serializer.instance = inscripcion


@extend_schema(tags=["VAT - Vouchers"])
class VoucherViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    """
    ViewSet for Voucher management.
    Supports filtering by ciudadano_id, estado, programa_id.
    """

    queryset = (
        Voucher.objects.select_related("ciudadano", "programa")
        .prefetch_related("recargas", "usos")
        .order_by("-fecha_asignacion")
    )
    serializer_class = VoucherSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        ciudadano_id = self.request.query_params.get("ciudadano_id")
        estado = self.request.query_params.get("estado")
        programa_id = self.request.query_params.get("programa_id")

        if ciudadano_id:
            queryset = queryset.filter(ciudadano_id=ciudadano_id)
        if estado:
            queryset = queryset.filter(estado=estado)
        if programa_id:
            queryset = queryset.filter(programa_id=programa_id)

        return queryset

    @action(detail=True, methods=["get"])
    def disponible(self, request, pk=None):
        """Get available credit for a voucher."""
        voucher = self.get_object()
        return Response(
            {
                "voucher_id": voucher.id,
                "cantidad_disponible": voucher.cantidad_disponible,
                "cantidad_usada": voucher.cantidad_usada,
                "cantidad_inicial": voucher.cantidad_inicial,
                "estado": voucher.estado,
            }
        )

    @action(detail=False, methods=["get"])
    def por_ciudadano(self, request):
        """Get vouchers for a specific citizen."""
        ciudadano_id = request.query_params.get("ciudadano_id")
        if not ciudadano_id:
            return Response(
                {"error": "ciudadano_id es requerido"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        vouchers = self.queryset.filter(ciudadano_id=ciudadano_id)
        serializer = self.get_serializer(vouchers, many=True)
        return Response(serializer.data)


# Phase 2 - Institución (Institution-related ViewSets)


@extend_schema(tags=["VAT - Institución"])
class InstitucionContactoViewSet(viewsets.ModelViewSet):
    queryset = InstitucionContacto.objects.select_related("centro").order_by("tipo")
    serializer_class = InstitucionContactoSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        centro_id = self.request.query_params.get("centro_id")
        tipo = self.request.query_params.get("tipo")
        if centro_id:
            queryset = queryset.filter(centro_id=centro_id)
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        return queryset


@extend_schema(tags=["VAT - Institución"])
class InstitucionIdentificadorHistViewSet(viewsets.ModelViewSet):
    queryset = InstitucionIdentificadorHist.objects.select_related("centro").order_by(
        "-vigencia_desde"
    )
    serializer_class = InstitucionIdentificadorHistSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        centro_id = self.request.query_params.get("centro_id")
        tipo_identificador = self.request.query_params.get("tipo_identificador")
        if centro_id:
            queryset = queryset.filter(centro_id=centro_id)
        if tipo_identificador:
            queryset = queryset.filter(tipo_identificador=tipo_identificador)
        return queryset


@extend_schema(tags=["VAT - Institución"])
class InstitucionUbicacionViewSet(viewsets.ModelViewSet):
    queryset = InstitucionUbicacion.objects.select_related(
        "centro", "localidad"
    ).order_by("rol_ubicacion")
    serializer_class = InstitucionUbicacionSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        centro_id = self.request.query_params.get("centro_id")
        rol_ubicacion = self.request.query_params.get("rol_ubicacion")
        if centro_id:
            queryset = queryset.filter(centro_id=centro_id)
        if rol_ubicacion:
            queryset = queryset.filter(rol_ubicacion=rol_ubicacion)
        return queryset


@extend_schema(
    tags=["VAT - Cursos"],
    summary="Cursos operativos de VAT",
    description=(
        "Expone el catálogo operativo de cursos asociado a centros. "
        "Este endpoint representa el nivel curso dentro del flujo real de VAT "
        "y se usa como paso previo para consultar sus comisiones en "
        "`/api/vat/comisiones-curso/`."
    ),
    parameters=[
        OpenApiParameter(
            "centro_id",
            OpenApiTypes.INT,
            OpenApiParameter.QUERY,
            description="Filtra cursos por centro.",
        ),
        OpenApiParameter(
            "provincia_id",
            OpenApiTypes.INT,
            OpenApiParameter.QUERY,
            description="Filtra cursos por provincia del centro.",
        ),
        OpenApiParameter(
            "municipio_id",
            OpenApiTypes.INT,
            OpenApiParameter.QUERY,
            description="Filtra cursos por municipio del centro.",
        ),
        OpenApiParameter(
            "modalidad_id",
            OpenApiTypes.INT,
            OpenApiParameter.QUERY,
            description="Filtra cursos por modalidad.",
        ),
        OpenApiParameter(
            "programa_id",
            OpenApiTypes.INT,
            OpenApiParameter.QUERY,
            description="Filtra cursos por programa.",
        ),
        OpenApiParameter(
            "estado",
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            description="Filtra cursos por estado.",
        ),
    ],
)
class CursoViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    queryset = (
        Curso.objects.select_related("centro", "modalidad")
        .prefetch_related(
            Prefetch(
                "voucher_parametrias",
                queryset=VoucherParametria.objects.select_related("programa").order_by(
                    "programa_id", "id"
                ),
            )
        )
        .order_by("-fecha_creacion", "nombre")
    )
    serializer_class = CursoSerializer
    permission_classes = [HasAPIKey]

    def _apply_curso_filters(self, queryset):
        centro_id = self.request.query_params.get("centro_id")
        provincia_id = self.request.query_params.get("provincia_id")
        municipio_id = self.request.query_params.get("municipio_id")
        modalidad_id = self.request.query_params.get("modalidad_id")
        programa_id = self.request.query_params.get("programa_id")
        estado = self.request.query_params.get("estado")
        if centro_id:
            queryset = queryset.filter(centro_id=centro_id)
        if provincia_id:
            queryset = queryset.filter(centro__provincia_id=provincia_id)
        if municipio_id:
            queryset = queryset.filter(centro__municipio_id=municipio_id)
        if modalidad_id:
            queryset = queryset.filter(modalidad_id=modalidad_id)
        if programa_id:
            queryset = (
                queryset.annotate(
                    programas_distintos=Count(
                        "voucher_parametrias__programa_id",
                        distinct=True,
                    )
                )
                .filter(
                    voucher_parametrias__programa_id=programa_id,
                    programas_distintos=1,
                )
                .distinct()
            )
        if estado:
            queryset = queryset.filter(estado=estado)
        return queryset

    def _get_busqueda_queryset(self):
        return (
            self._apply_curso_filters(Curso.objects.all())
            .select_related(
                "centro",
                "centro__provincia",
                "centro__municipio",
                "centro__localidad",
                "plan_estudio",
                "modalidad",
            )
            .prefetch_related(
                Prefetch(
                    "voucher_parametrias",
                    queryset=VoucherParametria.objects.select_related("programa").order_by(
                        "programa_id", "id"
                    ),
                ),
                Prefetch(
                    "comisiones",
                    queryset=(
                        ComisionCurso.objects.select_related(
                            "ubicacion",
                            "ubicacion__localidad",
                            "ubicacion__localidad__municipio",
                            "ubicacion__localidad__municipio__provincia",
                        )
                        .prefetch_related(
                            "horarios__dia_semana",
                            "sesiones__horario__dia_semana",
                            Prefetch(
                                "inscripciones",
                                queryset=Inscripcion.objects.only("id"),
                                to_attr="inscripciones_prefetch",
                            ),
                        )
                        .order_by("fecha_inicio", "codigo_comision")
                    )
                ),
            )
            .order_by("-fecha_creacion", "nombre")
        )

    def get_queryset(self):
        return self._apply_curso_filters(super().get_queryset())

    @extend_schema(
        tags=["VAT - Cursos"],
        summary="Buscar cursos operativos por texto",
        description=(
            "Busca cursos operativos por texto libre en nombre de curso, plan de estudio o "
            "título de referencia y devuelve la información enriquecida del curso, su centro, "
            "geografía y las comisiones con horarios y cupos. "
            "Ejemplo base: `/api/vat/cursos/buscar/?q=Her`. "
            "También admite los filtros opcionales de cursos, por ejemplo "
            "`/api/vat/cursos/buscar/?q=Her&centro_id=12&estado=activo`."
        ),
        parameters=[
            OpenApiParameter(
                "q",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                description=(
                    "Texto a buscar en nombre de curso, plan o título. "
                    "Debe tener al menos 3 caracteres."
                ),
                required=True,
            ),
            OpenApiParameter(
                "centro_id",
                OpenApiTypes.INT,
                OpenApiParameter.QUERY,
                description="Filtra cursos por centro.",
            ),
            OpenApiParameter(
                "provincia_id",
                OpenApiTypes.INT,
                OpenApiParameter.QUERY,
                description="Filtra cursos por provincia del centro.",
            ),
            OpenApiParameter(
                "municipio_id",
                OpenApiTypes.INT,
                OpenApiParameter.QUERY,
                description="Filtra cursos por municipio del centro.",
            ),
            OpenApiParameter(
                "modalidad_id",
                OpenApiTypes.INT,
                OpenApiParameter.QUERY,
                description="Filtra cursos por modalidad.",
            ),
            OpenApiParameter(
                "programa_id",
                OpenApiTypes.INT,
                OpenApiParameter.QUERY,
                description="Filtra cursos por programa.",
            ),
            OpenApiParameter(
                "estado",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                description="Filtra cursos por estado.",
            ),
        ],
        responses=CursoBusquedaSerializer(many=True),
        examples=[
            OpenApiExample(
                "Búsqueda exitosa paginada",
                value={
                    "count": 1,
                    "next": None,
                    "previous": None,
                    "results": [
                        {
                            "id": 120,
                            "nombre": "Herramientas Digitales",
                            "prioritario": True,
                            "estado": "activo",
                            "observaciones": None,
                            "fecha_creacion": "2026-04-12T10:00:00Z",
                            "fecha_modificacion": "2026-04-12T10:00:00Z",
                            "usa_voucher": True,
                            "costo_creditos": 2,
                            "centro": {
                                "id": 12,
                                "nombre": "CFP 401",
                                "referente": None,
                                "referente_nombre": "",
                                "codigo": "CFP-401",
                                "activo": True,
                                "provincia": {
                                    "id": 2,
                                    "nombre": "Buenos Aires"
                                },
                                "ciudad": {
                                    "provincia": {
                                        "id": 2,
                                        "nombre": "Buenos Aires"
                                    },
                                    "municipio": {
                                        "id": 15,
                                        "nombre": "La Plata",
                                        "provincia": 2,
                                        "provincia_nombre": "Buenos Aires"
                                    },
                                    "localidad": {
                                        "id": 120,
                                        "nombre": "Tolosa",
                                        "municipio": 15,
                                        "municipio_nombre": "La Plata",
                                        "provincia_nombre": "Buenos Aires"
                                    },
                                    "direccion": "Calle 1 Nro 123"
                                },
                                "telefono": "221-4000000",
                                "celular": "221-4000001",
                                "correo": "cfp401@example.org",
                                "nombre_referente": "Ana",
                                "apellido_referente": "Perez",
                                "tipo_gestion": "Estatal",
                                "clase_institucion": "Formación Profesional",
                                "situacion": "Institución de ETP"
                            },
                            "plan_estudio": 30,
                            "plan_estudio_nombre": "Herramientas Digitales I",
                            "modalidad": 1,
                            "modalidad_nombre": "Presencial",
                            "programa": {
                                "id": 7,
                                "nombre": "Programa Prioridad Formación"
                            },
                            "voucher_parametrias": [],
                            "comisiones": []
                        }
                    ]
                },
                response_only=True,
            ),
            OpenApiExample(
                "Error por texto corto",
                value={"q": ["Debe enviar al menos 3 caracteres para buscar."]},
                response_only=True,
                status_codes=["400"],
            ),
        ],
    )
    @action(detail=False, methods=["get"], url_path="buscar")
    def buscar(self, request, *args, **kwargs):
        texto = (request.query_params.get("q") or "").strip()
        if not texto:
            raise ValidationError({"q": ["Debe enviar un texto de búsqueda."]})
        if len(texto) < 3:
            raise ValidationError(
                {"q": ["Debe enviar al menos 3 caracteres para buscar."]}
            )

        queryset = (
            self._get_busqueda_queryset()
            .filter(
                Q(nombre__icontains=texto)
                | Q(plan_estudio__nombre__icontains=texto)
                | Q(plan_estudio__titulos__nombre__icontains=texto)
            )
            .distinct()
        )

        page = self.paginate_queryset(queryset)
        serializer = CursoBusquedaSerializer(page or queryset, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @extend_schema(
        tags=["VAT - Cursos"],
        summary="Listar cursos prioritarios",
        description=(
            "Devuelve los cursos operativos marcados como prioritarios con la misma "
            "información enriquecida del buscador de cursos. "
            "Ejemplo base: `/api/vat/cursos/prioritarios/`. "
            "También admite filtros opcionales como `centro_id`, `provincia_id`, `municipio_id`, "
            "`modalidad_id`, `programa_id` y `estado`."
        ),
        responses=CursoBusquedaSerializer(many=True),
        parameters=[
            OpenApiParameter(
                "centro_id",
                OpenApiTypes.INT,
                OpenApiParameter.QUERY,
                description="Filtra cursos por centro.",
            ),
            OpenApiParameter(
                "provincia_id",
                OpenApiTypes.INT,
                OpenApiParameter.QUERY,
                description="Filtra cursos por provincia del centro.",
            ),
            OpenApiParameter(
                "municipio_id",
                OpenApiTypes.INT,
                OpenApiParameter.QUERY,
                description="Filtra cursos por municipio del centro.",
            ),
            OpenApiParameter(
                "modalidad_id",
                OpenApiTypes.INT,
                OpenApiParameter.QUERY,
                description="Filtra cursos por modalidad.",
            ),
            OpenApiParameter(
                "programa_id",
                OpenApiTypes.INT,
                OpenApiParameter.QUERY,
                description="Filtra cursos por programa.",
            ),
            OpenApiParameter(
                "estado",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                description="Filtra cursos por estado.",
            ),
        ],
        examples=[
            OpenApiExample(
                "Listado de prioritarios paginado",
                value={
                    "count": 1,
                    "next": None,
                    "previous": None,
                    "results": [
                        {
                            "id": 140,
                            "nombre": "Herramientas de Gestión Prioritaria",
                            "prioritario": True,
                            "estado": "activo",
                            "observaciones": None,
                            "fecha_creacion": "2026-04-12T10:00:00Z",
                            "fecha_modificacion": "2026-04-12T10:00:00Z",
                            "usa_voucher": True,
                            "costo_creditos": 3,
                            "centro": {
                                "id": 12,
                                "nombre": "CFP 401",
                                "referente": None,
                                "referente_nombre": "",
                                "codigo": "CFP-401",
                                "activo": True,
                                "provincia": {
                                    "id": 2,
                                    "nombre": "Buenos Aires"
                                },
                                "ciudad": {
                                    "provincia": {
                                        "id": 2,
                                        "nombre": "Buenos Aires"
                                    },
                                    "municipio": {
                                        "id": 15,
                                        "nombre": "La Plata",
                                        "provincia": 2,
                                        "provincia_nombre": "Buenos Aires"
                                    },
                                    "localidad": {
                                        "id": 120,
                                        "nombre": "Tolosa",
                                        "municipio": 15,
                                        "municipio_nombre": "La Plata",
                                        "provincia_nombre": "Buenos Aires"
                                    },
                                    "direccion": "Calle 1 Nro 123"
                                },
                                "telefono": "221-4000000",
                                "celular": "221-4000001",
                                "correo": "cfp401@example.org",
                                "nombre_referente": "Ana",
                                "apellido_referente": "Perez",
                                "tipo_gestion": "Estatal",
                                "clase_institucion": "Formación Profesional",
                                "situacion": "Institución de ETP"
                            },
                            "plan_estudio": 30,
                            "plan_estudio_nombre": "Gestión Administrativa",
                            "modalidad": 1,
                            "modalidad_nombre": "Presencial",
                            "programa": {
                                "id": 7,
                                "nombre": "Programa Prioridad Formación"
                            },
                            "voucher_parametrias": [],
                            "comisiones": []
                        }
                    ]
                },
                response_only=True,
            )
        ],
    )
    @action(detail=False, methods=["get"], url_path="prioritarios")
    def prioritarios(self, request, *args, **kwargs):
        queryset = self._get_busqueda_queryset().filter(prioritario=True)

        page = self.paginate_queryset(queryset)
        serializer = CursoBusquedaSerializer(page or queryset, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)


@extend_schema(
    tags=["VAT - Cursos"],
    summary="Comisiones operativas de curso",
    description=(
        "Expone las aperturas concretas de `ComisionCurso` para los cursos operativos "
        "de VAT. Este es el endpoint que debe usarse para consultar comisiones reales de cursos; "
        "la ruta legacy `/api/vat/comisiones/` corresponde a oferta institucional y no al flujo "
        "operativo actual de cursos."
    ),
    parameters=[
        OpenApiParameter(
            "curso_id",
            OpenApiTypes.INT,
            OpenApiParameter.QUERY,
            description="Filtra comisiones por curso.",
        ),
        OpenApiParameter(
            "centro_id",
            OpenApiTypes.INT,
            OpenApiParameter.QUERY,
            description="Filtra comisiones por centro (via curso).",
        ),
        OpenApiParameter(
            "provincia_id",
            OpenApiTypes.INT,
            OpenApiParameter.QUERY,
            description="Filtra comisiones por provincia del centro del curso.",
        ),
        OpenApiParameter(
            "municipio_id",
            OpenApiTypes.INT,
            OpenApiParameter.QUERY,
            description="Filtra comisiones por municipio del centro del curso.",
        ),
        OpenApiParameter(
            "estado",
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            description="Filtra comisiones de curso por estado.",
        ),
    ],
)
class ComisionCursoViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    queryset = (
        ComisionCurso.objects.select_related("curso", "curso__centro", "ubicacion")
        .prefetch_related(
            "horarios__dia_semana",
            "sesiones__horario__dia_semana",
        )
        .order_by("codigo_comision")
    )
    serializer_class = ComisionCursoSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        curso_id = self.request.query_params.get("curso_id")
        centro_id = self.request.query_params.get("centro_id")
        provincia_id = self.request.query_params.get("provincia_id")
        municipio_id = self.request.query_params.get("municipio_id")
        estado = self.request.query_params.get("estado")
        if curso_id:
            queryset = queryset.filter(curso_id=curso_id)
        if centro_id:
            queryset = queryset.filter(curso__centro_id=centro_id)
        if provincia_id:
            queryset = queryset.filter(curso__centro__provincia_id=provincia_id)
        if municipio_id:
            queryset = queryset.filter(curso__centro__municipio_id=municipio_id)
        if estado:
            queryset = queryset.filter(estado=estado)
        return queryset


# Phase 4 - Oferta Institucional


@extend_schema(tags=["VAT - Oferta Institucional"])
class OfertaInstitucionalViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    queryset = OfertaInstitucional.objects.select_related(
        "centro", "plan_curricular"
    ).order_by("-fecha_publicacion")
    serializer_class = OfertaInstitucionalSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        centro_id = self.request.query_params.get("centro_id")
        estado = self.request.query_params.get("estado")
        if centro_id:
            queryset = queryset.filter(centro_id=centro_id)
        if estado:
            queryset = queryset.filter(estado=estado)
        return queryset


@extend_schema(tags=["VAT - Oferta Institucional"])
class ComisionViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    queryset = (
        Comision.objects.select_related("oferta")
        .prefetch_related("horarios")
        .order_by("nombre")
    )
    serializer_class = ComisionSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        oferta_id = self.request.query_params.get("oferta_id")
        estado = self.request.query_params.get("estado")
        if oferta_id:
            queryset = queryset.filter(oferta_id=oferta_id)
        if estado:
            queryset = queryset.filter(estado=estado)
        return queryset


@extend_schema(tags=["VAT - Oferta Institucional"])
class ComisionHorarioViewSet(viewsets.ModelViewSet):
    queryset = ComisionHorario.objects.select_related("comision").order_by(
        "dia_semana", "hora_desde"
    )
    serializer_class = ComisionHorarioSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        comision_id = self.request.query_params.get("comision_id")
        if comision_id:
            queryset = queryset.filter(comision_id=comision_id)
        return queryset


# Phase 5 - Inscripciones


@extend_schema(tags=["VAT - Inscripciones"])
class InscripcionViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    queryset = Inscripcion.objects.select_related(
        "ciudadano",
        "programa",
        "comision",
        "comision_curso",
        "comision_curso__curso",
    ).order_by("-fecha_inscripcion")
    serializer_class = InscripcionSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        ciudadano_id = self.request.query_params.get("ciudadano_id")
        comision_id = self.request.query_params.get("comision_id")
        comision_curso_id = self.request.query_params.get("comision_curso_id")
        estado = self.request.query_params.get("estado")
        if ciudadano_id:
            queryset = queryset.filter(ciudadano_id=ciudadano_id)
        if comision_id:
            queryset = queryset.filter(comision_id=comision_id)
        if comision_curso_id:
            queryset = queryset.filter(comision_curso_id=comision_curso_id)
        if estado:
            queryset = queryset.filter(estado=estado)
        return queryset

    def perform_create(self, serializer):
        data = serializer.validated_data
        comision = data.get("comision") or data.get("comision_curso")
        if comision is None:
            raise ValidationError(
                {"comision": ["Debe enviar una comisión o una comisión de curso."]}
            )
        try:
            inscripcion = InscripcionService.crear_inscripcion(
                ciudadano=data["ciudadano"],
                comision=comision,
                programa=data.get("programa"),
                estado=data.get("estado", "inscripta"),
                origen_canal=data.get("origen_canal", "api"),
                observaciones=data.get("observaciones", ""),
                usuario=getattr(self.request, "user", None),
            )
        except ValueError as exc:
            raise ValidationError({"error": [str(exc)]}) from exc

        serializer.instance = inscripcion


@extend_schema(
    tags=["VAT - Cursos"],
    summary="Inscripciones sobre comisiones de curso",
    description=(
        "Endpoint explícito para crear y listar inscripciones vinculadas a `ComisionCurso`. "
        "Se documenta por separado para que Swagger muestre con claridad el flujo operativo de cursos "
        "sin mezclarlo con la ruta general `/api/vat/inscripciones/`."
    ),
)
class InscripcionCursoViewSet(InscripcionViewSet):
    def get_queryset(self):
        return super().get_queryset().filter(comision_curso__isnull=False)

    def perform_create(self, serializer):
        if serializer.validated_data.get("comision") is not None:
            raise ValidationError(
                {
                    "comision_curso": [
                        "Este endpoint solo admite inscripciones sobre comisiones de curso."
                    ]
                }
            )
        return super().perform_create(serializer)


# Phase 7 - Evaluaciones


@extend_schema(tags=["VAT - Evaluaciones"])
class EvaluacionViewSet(viewsets.ModelViewSet):
    queryset = (
        Evaluacion.objects.select_related("comision")
        .prefetch_related("resultados")
        .order_by("-fecha")
    )
    serializer_class = EvaluacionSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        comision_id = self.request.query_params.get("comision_id")
        tipo = self.request.query_params.get("tipo")
        if comision_id:
            queryset = queryset.filter(comision_id=comision_id)
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        return queryset


@extend_schema(tags=["VAT - Evaluaciones"])
class ResultadoEvaluacionViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    queryset = ResultadoEvaluacion.objects.select_related("evaluacion").order_by("id")
    serializer_class = ResultadoEvaluacionSerializer
    permission_classes = [HasAPIKey]

    def get_queryset(self):
        queryset = super().get_queryset()
        evaluacion_id = self.request.query_params.get("evaluacion_id")
        calificacion = self.request.query_params.get("calificacion")
        if evaluacion_id:
            queryset = queryset.filter(evaluacion_id=evaluacion_id)
        if calificacion:
            queryset = queryset.filter(calificacion=calificacion)
        return queryset
