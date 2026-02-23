"""
URLs para la API REST de Comunicados.
"""

from rest_framework.routers import SimpleRouter
from .api_views import ComunicadoInstitucionalViewSet, ComunicadoComedorViewSet

router = SimpleRouter()
router.register(
    r"institucional",
    ComunicadoInstitucionalViewSet,
    basename="comunicados-institucional",
)
router.register(
    r"comedor/(?P<comedor_id>\d+)",
    ComunicadoComedorViewSet,
    basename="comunicados-comedor",
)

urlpatterns = router.urls
