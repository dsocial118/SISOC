from django.urls import path

from anexos.views.api_views import AnexoSocioProductivoViewSet

urlpatterns = [
    path(
        "api/anexos-socioproductivos/",
        AnexoSocioProductivoViewSet.as_view({"get": "list"}),
        name="anexos_socioproductivos_list",
    ),
    path(
        "api/anexos_socioproductivos/<int:pk>/",
        AnexoSocioProductivoViewSet.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
            }
        ),
        name="anexos_socioproductivos_detail",
    ),
]
