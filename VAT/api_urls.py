from django.urls import path, include
from rest_framework.routers import DefaultRouter
from VAT.api_views import (
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
    ProvinciaViewSet,
    MunicipioViewSet,
    LocalidadViewSet,
)

router = DefaultRouter()
router.register(r"centros", CentroViewSet, basename="vat-api-centro")
router.register(r"actividades", ActividadViewSet, basename="vat-api-actividad")
router.register(r"categorias", CategoriaViewSet, basename="vat-api-categoria")
router.register(
    r"actividades-centro", ActividadCentroViewSet, basename="vat-api-actividad-centro"
)
router.register(
    r"participantes", ParticipanteActividadViewSet, basename="vat-api-participante"
)
router.register(r"beneficiarios", BeneficiarioViewSet, basename="vat-api-beneficiario")
router.register(r"responsables", ResponsableViewSet, basename="vat-api-responsable")
router.register(
    r"beneficiario-responsable",
    BeneficiarioResponsableViewSet,
    basename="vat-api-beneficiario-responsable",
)
router.register(
    r"cabal-registros", InformeCabalRegistroViewSet, basename="vat-api-cabal-registro"
)
router.register(
    r"cabal-archivos", CabalArchivoViewSet, basename="vat-api-cabal-archivo"
)

router.register(r"provincias", ProvinciaViewSet, basename="vat-api-provincia")
router.register(r"municipios", MunicipioViewSet, basename="vat-api-municipio")
router.register(r"localidades", LocalidadViewSet, basename="vat-api-localidad")

urlpatterns = [
    path("", include(router.urls)),
]
