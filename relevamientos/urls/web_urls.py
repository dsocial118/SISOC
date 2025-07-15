from django.urls import path
from core.decorators import group_required
from relevamientos.views.web_views import (
    RelevamientoCreateView,
    RelevamientoDeleteView,
    RelevamientoDetailView,
    RelevamientoListView,
    RelevamientoUpdateView,
)

urlpatterns = [
    path(
        "comedores/<comedor_pk>/relevamiento/listar",
        group_required(["Comedores Relevamiento Ver"])(RelevamientoListView.as_view()),
        name="relevamientos",
    ),
    path(
        "comedores/<comedor_pk>/relevamiento/crear",
        group_required(["Comedores Relevamiento Crear"])(
            RelevamientoCreateView.as_view()
        ),
        name="relevamiento_crear",
    ),
    path(
        "comedores/<comedor_pk>/relevamiento/<int:pk>",
        group_required(["Comedores Relevamiento Detalle"])(
            RelevamientoDetailView.as_view()
        ),
        name="relevamiento_detalle",
    ),
    path(
        "comedores/<comedor_pk>/relevamiento/<int:pk>/editar",
        group_required(["Comedores Relevamiento Editar"])(
            RelevamientoUpdateView.as_view()
        ),
        name="relevamiento_editar",
    ),
    path(
        "comedores/<comedor_pk>/relevamiento/<int:pk>/eliminar",
        group_required(["Comedores Relevamiento Editar"])(
            RelevamientoDeleteView.as_view()
        ),
        name="relevamiento_eliminar",
    ),
]
