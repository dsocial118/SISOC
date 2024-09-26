from django.urls import path
from django.contrib.auth.decorators import login_required

from comedores.views import (
    ComedorListView,
    ComedorCreateView,
    ComedorDetailView,
    ComedorUpdateView,
    RelevamientoCreateView,
    RelevamientoDetailView,
    RelevamientoUpdateView,
    RelevamientoDeleteView,
    ComedorDeleteView,
    ObservacionCreateView,
    ObservacionDetailView,
    ObservacionUpdateView,
    ObservacionDeleteView,
)


urlpatterns = [
    path(
        "comedores/listar",
        login_required(ComedorListView.as_view()),
        name="comedores",
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
        login_required(ComedorDeleteView.as_view()),
        name="comedor_eliminar",
    ),
    path(
        "comedores/<comedor_pk>/relevamiento/crear",
        login_required(RelevamientoCreateView.as_view()),
        name="relevamiento_crear",
    ),
    path(
        "comedores/<comedor_pk>/relevamiento/<pk>",
        login_required(RelevamientoDetailView.as_view()),
        name="relevamiento_detalle",
    ),
    path(
        "comedores/<comedor_pk>/relevamiento/<pk>/editar",
        login_required(RelevamientoUpdateView.as_view()),
        name="relevamiento_editar",
    ),
    path(
        "comedores/<comedor_pk>/relevamiento/<pk>/eliminar",
        login_required(RelevamientoDeleteView.as_view()),
        name="relevamiento_eliminar",
    ),
    path(
        "comedores/<comedor_pk>/observacion/crear",
        login_required(ObservacionCreateView.as_view()),
        name="observacion_crear",
    ),
    path(
        "comedores/<comedor_pk>/observacion/<pk>",
        login_required(ObservacionDetailView.as_view()),
        name="observacion_detalle",
    ),
    path(
        "comedores/<comedor_pk>/observacion/<pk>/editar",
        login_required(ObservacionUpdateView.as_view()),
        name="observacion_editar",
    ),
    path(
        "comedores/<comedor_pk>/observacion/<pk>/eliminar",
        login_required(ObservacionDeleteView.as_view()),
        name="observacion_eliminar",
    ),
]
