from django.urls import path
from expedientespagos import views

urlpatterns = [
    path(
        "expedientespagos/",
        views.ExpedientesPagosListView.as_view(),
        name="expedientespagos_list",
    ),
    path(
        "expedientespagos/<int:pk>/",
        views.ExpedientesPagosDetailView.as_view(),
        name="expedientespagos_detail",
    ),
    path(
        "expedientespagos/nuevo/",
        views.ExpedientesPagosCreateView.as_view(),
        name="expedientespagos_create",
    ),
    path(
        "expedientespagos/<int:pk>/editar/",
        views.ExpedientesPagosUpdateView.as_view(),
        name="expedientespagos_update",
    ),
    path(
        "expedientespagos/<int:pk>/eliminar/",
        views.ExpedientesPagosDeleteView.as_view(),
        name="expedientespagos_delete",
    ),
]