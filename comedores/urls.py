from django.urls import path
from django.contrib.auth.decorators import login_required

from comedores.views import ComedorListView, ComedorCreateView, ComedorDetailView


urlpatterns = [
    path(
        "comedores/listar",
        login_required(ComedorListView.as_view()),
        name="comedor_listar",
    ),
    path(
        "comedores/crear",
        login_required(ComedorCreateView.as_view()),
        name="comedor_crear",
    ),
    path(
        "comedores/ver/<pk>",
        login_required(ComedorDetailView.as_view()),
        name="comedor_ver",
    ),
    path(
        "comedores/editar/<pk>",
        login_required(ComedorDetailView.as_view()),
        name="comedor_editar",
    ),
    path(
        "comedores/eliminar/<pk>",
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
]
