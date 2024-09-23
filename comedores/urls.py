from django.urls import path
from django.contrib.auth.decorators import login_required

from comedores.views import (
    ComedorListView,
    ComedorCreateView,
    ComedorDetailView,
    ComedorUpdateView,
    RelevamientoCreateView,
    RelevamientoDetailView,
)


urlpatterns = [
    path(
        "comedores",
        login_required(ComedorListView.as_view()),
        name="comedor_listar",
    ),
    path(
        "comedores/crear",
        login_required(ComedorCreateView.as_view()),
        name="comedor_crear",
    ),
    path(
        "comedores/<pk>",
        login_required(ComedorDetailView.as_view()),
        name="comedor_detalle",
    ),
    path(
        "comedores/<pk>/editar",
        login_required(ComedorUpdateView.as_view()),
        name="comedor_editar",
    ),
    path(
        "comedores/<pk>/eliminar",
        login_required(ComedorDetailView.as_view()),
        name="comedor_eliminar",
    ),
    path(
        "comedores/<pk>/relevamientos",
        login_required(ComedorListView.as_view()),
        name="comedor_relevamientos",
    ),
    path(
        "comedores/<pk>/observaciones",
        login_required(ComedorListView.as_view()),
        name="comedor_observaciones",
    ),
    path(
        "comedores/<pk>/relevamientos/crear",
        login_required(RelevamientoCreateView.as_view()),
        name="relevamiento_crear",
    ),
    path(
        "relevamientos/<pk>",
        login_required(RelevamientoDetailView.as_view()),
        name="relevamiento_detalle",
    ),
    path(
        "relevamientos/<pk>/editar",
        login_required(RelevamientoDetailView.as_view()),
        name="relevamiento_editar",
    ),
    path(
        "relevamientos/<pk>/eliminar",
        login_required(RelevamientoDetailView.as_view()),
        name="relevamiento_eliminar",
    ),
]
