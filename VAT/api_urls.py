from django.urls import path, include
from rest_framework.routers import DefaultRouter
from VAT.api_views import (
    CentroViewSet,
    ProvinciaViewSet,
    MunicipioViewSet,
    LocalidadViewSet,
    ModalidadInstitucionalViewSet,
    SectorViewSet,
    SubsectorViewSet,
    TituloReferenciaViewSet,
    ModalidadCursadaViewSet,
    PlanVersionCurricularViewSet,
    InscripcionOfertaViewSet,
    VoucherViewSet,
    InstitucionContactoViewSet,
    InstitucionIdentificadorHistViewSet,
    InstitucionUbicacionViewSet,
    CursoViewSet,
    ComisionCursoViewSet,
    OfertaInstitucionalViewSet,
    ComisionViewSet,
    ComisionHorarioViewSet,
    InscripcionViewSet,
    InscripcionCursoViewSet,
    EvaluacionViewSet,
    ResultadoEvaluacionViewSet,
)
from VAT.api_web_views import (
    VatWebCentroViewSet,
    VatWebCiudadanoViewSet,
    VatWebCursoViewSet,
    VatWebInscripcionViewSet,
    VatWebTituloViewSet,
)

router = DefaultRouter()
router.register(r"centros", CentroViewSet, basename="vat-api-centro")
router.register(r"provincias", ProvinciaViewSet, basename="vat-api-provincia")
router.register(r"municipios", MunicipioViewSet, basename="vat-api-municipio")
router.register(r"localidades", LocalidadViewSet, basename="vat-api-localidad")
router.register(
    r"modalidades-institucionales",
    ModalidadInstitucionalViewSet,
    basename="vat-api-modalidad-institucional",
)
router.register(r"sectores", SectorViewSet, basename="vat-api-sector")
router.register(r"subsectores", SubsectorViewSet, basename="vat-api-subsector")
router.register(
    r"titulos-referencia", TituloReferenciaViewSet, basename="vat-api-titulo-referencia"
)
router.register(
    r"modalidades-cursadas",
    ModalidadCursadaViewSet,
    basename="vat-api-modalidad-cursada",
)
router.register(
    r"planes-curriculares",
    PlanVersionCurricularViewSet,
    basename="vat-api-plan-curricular",
)
router.register(
    r"inscripciones-oferta",
    InscripcionOfertaViewSet,
    basename="vat-api-inscripcion-oferta",
)
router.register(
    r"vouchers",
    VoucherViewSet,
    basename="vat-api-voucher",
)
# Phase 2 - Institución
router.register(
    r"institucion-contactos",
    InstitucionContactoViewSet,
    basename="vat-api-institucion-contacto",
)
router.register(
    r"institucion-identificadores",
    InstitucionIdentificadorHistViewSet,
    basename="vat-api-institucion-identificador",
)
router.register(
    r"institucion-ubicaciones",
    InstitucionUbicacionViewSet,
    basename="vat-api-institucion-ubicacion",
)
# Cursos (capa operativa)
router.register(
    r"cursos",
    CursoViewSet,
    basename="vat-api-curso",
)
router.register(
    r"comisiones-curso",
    ComisionCursoViewSet,
    basename="vat-api-comision-curso",
)
# Phase 4 - Oferta Institucional
router.register(
    r"ofertas-institucionales",
    OfertaInstitucionalViewSet,
    basename="vat-api-oferta-institucional",
)
router.register(
    r"comisiones",
    ComisionViewSet,
    basename="vat-api-comision",
)
router.register(
    r"comision-horarios",
    ComisionHorarioViewSet,
    basename="vat-api-comision-horario",
)
# Phase 5 - Inscripciones
router.register(
    r"inscripciones",
    InscripcionViewSet,
    basename="vat-api-inscripcion",
)
router.register(
    r"inscripciones-curso",
    InscripcionCursoViewSet,
    basename="vat-api-inscripcion-curso",
)
# Phase 7 - Evaluaciones
router.register(
    r"evaluaciones",
    EvaluacionViewSet,
    basename="vat-api-evaluacion",
)
router.register(
    r"resultado-evaluaciones",
    ResultadoEvaluacionViewSet,
    basename="vat-api-resultado-evaluacion",
)

router.register(r"web/centros", VatWebCentroViewSet, basename="vat-web-centro")
router.register(
    r"web/ciudadanos",
    VatWebCiudadanoViewSet,
    basename="vat-web-ciudadano",
)
router.register(r"web/titulos", VatWebTituloViewSet, basename="vat-web-titulo")
router.register(r"web/cursos", VatWebCursoViewSet, basename="vat-web-curso")
router.register(
    r"web/inscripciones",
    VatWebInscripcionViewSet,
    basename="vat-web-inscripcion",
)

urlpatterns = [
    path("", include(router.urls)),
]
