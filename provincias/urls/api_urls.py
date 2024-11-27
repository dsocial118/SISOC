from django.urls import path

from provincias.views.api_views import ProyectoViewSet, ProyectoSubsanarView

urlpatterns = [
    path(
        "api/proyecto/",
        ProyectoViewSet.as_view({"get": "list"}),
        name="anexos_socioproductivos_list",
    ),
    path(
        "api/proyecto/<int:pk>/",
        ProyectoViewSet.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
            }
        ),
        name="anexos_socioproductivos_detail",
    ),
    path(
        "api/proyecto/subsanar/<int:pk>/",
        ProyectoSubsanarView.as_view(),
        name="proyecto_subsanar",
    ),
]
