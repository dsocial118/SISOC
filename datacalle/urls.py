from django.urls import path

from core.decorators import permissions_any_required
from datacalle.views import (
    RelevamientoCreateView,
    RelevamientoDeleteView,
    RelevamientoDetailView,
    RelevamientoListView,
    RelevamientoUpdateView,
)

urlpatterns = [
    path(
        "datacalle/relevamientos/",
        permissions_any_required(["datacalle.view_relevamiento"])(
            RelevamientoListView.as_view()
        ),
        name="datacalle_relevamientos_listar",
    ),
    path(
        "datacalle/relevamientos/crear/",
        permissions_any_required(["datacalle.add_relevamiento"])(
            RelevamientoCreateView.as_view()
        ),
        name="datacalle_relevamientos_crear",
    ),
    path(
        "datacalle/relevamientos/<uuid:pk>/",
        permissions_any_required(["datacalle.view_relevamiento"])(
            RelevamientoDetailView.as_view()
        ),
        name="datacalle_relevamientos_detalle",
    ),
    path(
        "datacalle/relevamientos/<uuid:pk>/editar/",
        permissions_any_required(["datacalle.change_relevamiento"])(
            RelevamientoUpdateView.as_view()
        ),
        name="datacalle_relevamientos_editar",
    ),
    path(
        "datacalle/relevamientos/<uuid:pk>/eliminar/",
        permissions_any_required(["datacalle.delete_relevamiento"])(
            RelevamientoDeleteView.as_view()
        ),
        name="datacalle_relevamientos_eliminar",
    ),
]
