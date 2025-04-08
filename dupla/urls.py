from django.urls import path
from configuraciones.decorators import group_required
from dupla.views import (
    DuplaCreateView,
    DuplaDeleteView,
    DuplaDetailView,
    DuplaListView,
    DuplaUpdateView,
)

urlpatterns = [
    path(
        "dupla/",
        group_required("Dupla")(DuplaListView.as_view()),
        name="dupla_list",
    ),
    path(
        "dupla/crear/",
        group_required("Dupla")(DuplaCreateView.as_view()),
        name="dupla_crear",
    ),
    path(
        "dupla/<int:pk>/actualizar/",
        group_required("Dupla")(DuplaUpdateView.as_view()),
        name="dupla_actualizar",
    ),
    path(
        "dupla/<int:pk>/",
        group_required("Dupla")(DuplaDetailView.as_view()),
        name="dupla_detalle",
    ),
    path(
        "dupla/<int:pk>/eliminar/",
        group_required("Dupla")(DuplaDeleteView.as_view()),
        name="dupla_eliminar",
    ),


]