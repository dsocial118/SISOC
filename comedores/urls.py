from django.urls import path
from django.contrib.auth.decorators import login_required

from comedores.views import ComedorListView


urlpatterns = [
    path(
        "comedores/listar",
        login_required(ComedorListView.as_view()),
        name="comedor_listar",
    ),
    path(
        "comedores/crear",
        login_required(ComedorListView.as_view()),
        name="comedor_crear",
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
        "comedores/<pk>/observaciones",
        login_required(ComedorListView.as_view()),
        name="comedor_ver",
    ),
]
