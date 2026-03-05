from django.urls import path
from core.decorators import permissions_any_required
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
        permissions_any_required(["relevamientos.view_relevamiento"])(
            RelevamientoListView.as_view()
        ),
        name="relevamientos",
    ),
    path(
        "comedores/<comedor_pk>/relevamiento/crear",
        permissions_any_required(["relevamientos.add_relevamiento"])(
            RelevamientoCreateView.as_view()
        ),
        name="relevamiento_crear",
    ),
    path(
        "comedores/<comedor_pk>/relevamiento/<int:pk>",
        permissions_any_required(["relevamientos.view_relevamiento"])(
            RelevamientoDetailView.as_view()
        ),
        name="relevamiento_detalle",
    ),
    path(
        "comedores/<comedor_pk>/relevamiento/<int:pk>/editar",
        permissions_any_required(["relevamientos.change_relevamiento"])(
            RelevamientoUpdateView.as_view()
        ),
        name="relevamiento_editar",
    ),
    path(
        "comedores/<comedor_pk>/relevamiento/<int:pk>/eliminar",
        permissions_any_required(["relevamientos.change_relevamiento"])(
            RelevamientoDeleteView.as_view()
        ),
        name="relevamiento_eliminar",
    ),
]
