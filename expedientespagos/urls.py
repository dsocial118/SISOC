from django.urls import path
from configuraciones.decorators import group_required
from expedientespagos.views import (
    ExpedientesPagosListView,
    ExpedientesPagosDetailView,
    ExpedientesPagosCreateView,
    ExpedientesPagosUpdateView,
    ExpedientesPagosDeleteView,
)
urlpatterns = [
    path(
        "expedientespagos/<int:pk>/",
        ExpedientesPagosListView.as_view(),
        name="expedientespagos_list",
    ),
    path(
        "expedientespagos/<int:pk>/detalle/",
        ExpedientesPagosDetailView.as_view(),
        name="expedientespagos_detail",
    ),
    path(
        "expedientespagos/<int:pk>/nuevo/",
        group_required("Area Legales")(ExpedientesPagosCreateView.as_view()),
        name="expedientespagos_create",
    ),
    path(
        "expedientespagos/<int:pk>/editar/",
        group_required("Tecnico Comedor","Abogado Dupla")(ExpedientesPagosUpdateView.as_view()),
        name="expedientespagos_update",
    ),
    path(
        "expedientespagos/<int:pk>/eliminar/",
        group_required("Area Legales")(ExpedientesPagosDeleteView.as_view()),
        name="expedientespagos_delete",
    ),
]
