from django.urls import path
from core.decorators import group_required
from relevamientos.views.web_views import (
    RelevamientoDeleteView,
    RelevamientoDetailView,
    RelevamientoListView,
)

urlpatterns = [
    path(
        "comedores/<comedor_pk>/relevamiento/listar",
        group_required(["Comedores Relevamiento Ver"])(RelevamientoListView.as_view()),
        name="relevamientos",
    ),
    path(
        "comedores/<comedor_pk>/relevamiento/<int:pk>",
        group_required(["Comedores Relevamiento Detalle"])(
            RelevamientoDetailView.as_view()
        ),
        name="relevamiento_detalle",
    ),
    path(
        "comedores/<comedor_pk>/relevamiento/<int:pk>/eliminar",
        group_required(["Comedores Relevamiento Editar"])(
            RelevamientoDeleteView.as_view()
        ),
        name="relevamiento_eliminar",
    ),
]
