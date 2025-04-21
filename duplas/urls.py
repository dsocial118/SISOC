from django.urls import path
from configuraciones.decorators import group_required
from duplas.views import (
    DuplaCreateView,
    DuplaDeleteView,
    DuplaDetailView,
    DuplaListView,
    DuplaUpdateView,
)

urlpatterns = [
    path(
        "duplas/",
        group_required("Duplas")(DuplaListView.as_view()),
        name="dupla_list",
    ),
    path(
        "duplas/crear/",
        group_required("Duplas")(DuplaCreateView.as_view()),
        name="dupla_crear",
    ),
    path(
        "duplas/<int:pk>/editar/",
        group_required("Duplas")(DuplaUpdateView.as_view()),
        name="dupla_editar",
    ),
    path(
        "duplas/<int:pk>/",
        group_required("Duplas")(DuplaDetailView.as_view()),
        name="dupla_detalle",
    ),
    path(
        "duplas/<int:pk>/eliminar/",
        group_required("Duplas")(DuplaDeleteView.as_view()),
        name="dupla_eliminar",
    ),
]
