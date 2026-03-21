from django.urls import path, include
from rest_framework.routers import DefaultRouter
from VAT.api_views import (
    CentroViewSet,
    ActividadViewSet,
    CategoriaViewSet,
    ActividadCentroViewSet,
    ParticipanteActividadViewSet,
    ProvinciaViewSet,
    MunicipioViewSet,
    LocalidadViewSet,
    ModalidadInstitucionalViewSet,
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
router.register(r"provincias", ProvinciaViewSet, basename="vat-api-provincia")
router.register(r"municipios", MunicipioViewSet, basename="vat-api-municipio")
router.register(r"localidades", LocalidadViewSet, basename="vat-api-localidad")
router.register(
    r"modalidades-institucionales",
    ModalidadInstitucionalViewSet,
    basename="vat-api-modalidad-institucional",
)

urlpatterns = [
    path("", include(router.urls)),
]
