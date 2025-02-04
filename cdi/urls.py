from django.urls import path

from cdi.views import (
    CDIListView,
    CDICreateView,
    CDIDetailView,
    CDIUpdateView,
    CDIDeleteView,
)
from configuraciones.decorators import group_required

urlpatterns = [
    path(
        "cdi/listar",
        group_required("CDI")(CDIListView.as_view()),
        name="cdi",
    ),
    path(
        "cdi/crear",
        group_required("CDI")(CDICreateView.as_view()),
        name="cdi_crear",
    ),
    path(
        "cdi/detalle/<int:pk>",
        group_required("CDI")(CDIDetailView.as_view()),
        name="cdi_detalle",
    ),
    path(
        "cdi/editar/<int:pk>",
        group_required("CDI")(CDIUpdateView.as_view()),
        name="cdi_editar",
    ),
    path(
        "cdi/eliminar/<int:pk>",
        group_required("CDI")(CDIDeleteView.as_view()),
        name="cdi_eliminar",
    ),
]
