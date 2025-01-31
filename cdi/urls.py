from django.urls import path
from django.contrib.auth.decorators import login_required

from cdi.views import (
    CDIListView,
    CDICreateView,
    CDIDetailView,
    CDIUpdateView,
    CDIDeleteView,
)

urlpatterns = [
    path(
        "cdi/listar",
        login_required(CDIListView.as_view()),
        name="cdi",
    ),
    path(
        "cdi/crear",
        login_required(CDICreateView.as_view()),
        name="cdi_crear",
    ),
    path(
        "cdi/detalle/<int:pk>",
        login_required(CDIDetailView.as_view()),
        name="cdi_detalle",
    ),
        path(
        "cdi/editar/<int:pk>",
        login_required(CDIUpdateView.as_view()),
        name="cdi_editar",
    ),
        path(
        "cdi/eliminar/<int:pk>",
        login_required(CDIDeleteView.as_view()),
        name="cdi_eliminar",
    ),
]
