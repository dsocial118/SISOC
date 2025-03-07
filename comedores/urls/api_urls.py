from django.urls import path

from comedores.views.api_views import (
    RelevamientoApiView,
)

urlpatterns = [
    path(
        "api/relevamiento",
        RelevamientoApiView.as_view(),
        name="api_relevamiento",
    ),
]
