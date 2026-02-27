"""
URLs para API de core.
"""

from rest_framework.routers import DefaultRouter
from core.api_views import RenaperConsultaViewSet

router = DefaultRouter()
router.register(r"", RenaperConsultaViewSet, basename="renaper-consulta")

urlpatterns = router.urls
