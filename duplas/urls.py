from django.urls import path
from core.decorators import group_required
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
        group_required("Admin")(DuplaListView.as_view()),
        name="dupla_list",
    ),
    path(
        "duplas/crear/",
        group_required("Admin")(DuplaCreateView.as_view()),
        name="dupla_crear",
    ),
    path(
        "duplas/<int:pk>/editar/",
        group_required("Admin")(DuplaUpdateView.as_view()),
        name="dupla_editar",
    ),
    path(
        "duplas/<int:pk>/",
        group_required("Admin")(DuplaDetailView.as_view()),
        name="dupla_detalle",
    ),
    path(
        "duplas/<int:pk>/eliminar/",
        group_required("Admin")(DuplaDeleteView.as_view()),
        name="dupla_eliminar",
    ),
]
