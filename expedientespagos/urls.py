from django.urls import path
from core.decorators import permissions_any_required
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
        permissions_any_required(
            [
                "comedores.view_comedor",
                "admisiones.view_admision",
                "acompanamientos.view_informacionrelevante",
                "expedientespagos.view_expedientepago",
            ]
        )(ExpedientesPagosCreateView.as_view()),
        name="expedientespagos_create",
    ),
    path(
        "expedientespagos/<int:pk>/editar/",
        permissions_any_required(
            [
                "comedores.view_comedor",
                "admisiones.view_admision",
                "acompanamientos.view_informacionrelevante",
                "expedientespagos.view_expedientepago",
            ]
        )(ExpedientesPagosUpdateView.as_view()),
        name="expedientespagos_update",
    ),
    path(
        "expedientespagos/<int:pk>/eliminar/",
        permissions_any_required(
            [
                "comedores.view_comedor",
                "admisiones.view_admision",
                "acompanamientos.view_informacionrelevante",
                "expedientespagos.view_expedientepago",
            ]
        )(ExpedientesPagosDeleteView.as_view()),
        name="expedientespagos_delete",
    ),
]
