from django.urls import path, include
from rest_framework.routers import DefaultRouter
from centrodefamilia.api_views import (
    CentroViewSet,
    ActividadViewSet,
    CategoriaViewSet,
    ActividadCentroViewSet,
    ParticipanteActividadViewSet,
    BeneficiarioViewSet,
    ResponsableViewSet,
    BeneficiarioResponsableViewSet,
    InformeCabalRegistroViewSet,
    CabalArchivoViewSet,
)

router = DefaultRouter()
router.register(r"centros", CentroViewSet, basename="api-centro")
router.register(r"actividades", ActividadViewSet, basename="api-actividad")
router.register(r"categorias", CategoriaViewSet, basename="api-categoria")
router.register(
    r"actividades-centro", ActividadCentroViewSet, basename="api-actividad-centro"
)
router.register(
    r"participantes", ParticipanteActividadViewSet, basename="api-participante"
)
router.register(r"beneficiarios", BeneficiarioViewSet, basename="api-beneficiario")
router.register(r"responsables", ResponsableViewSet, basename="api-responsable")
router.register(
    r"beneficiario-responsable",
    BeneficiarioResponsableViewSet,
    basename="api-beneficiario-responsable",
)
router.register(
    r"cabal-registros", InformeCabalRegistroViewSet, basename="api-cabal-registro"
)
router.register(r"cabal-archivos", CabalArchivoViewSet, basename="api-cabal-archivo")

urlpatterns = [
    path("", include(router.urls)),
]
