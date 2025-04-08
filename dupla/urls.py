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
        group_required("Abogados"),
        DuplaListView.as_view(),
        name="dupla_list",
    ),
    path(
        "dupla/crear/",
        group_required("Abogados"),
        DuplaCreateView.as_view(),
        name="dupla_crear",
    ),
    path(
        "dupla/<int:pk>/actualizar/",
        group_required("Abogados"),
        DuplaUpdateView.as_view(),
        name="dupla_actualizar",
    ),
    path(
        "dupla/<int:pk>/",
        group_required("Abogados"),
        DuplaDetailView.as_view(),
        name="dupla_detalle",
    ),
    path(
        "dupla/<int:pk>/eliminar/",
        group_required("Abogados"),
        DuplaDeleteView.as_view(),
        name="dupla_eliminar",
    ),


]