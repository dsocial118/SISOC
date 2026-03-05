from django.urls import path

from core.decorators import permissions_any_required
from centrodeinfancia.views import (
    CentroDeInfanciaCreateView,
    CentroDeInfanciaDeleteView,
    CentroDeInfanciaDetailView,
    CentroDeInfanciaListView,
    CentroDeInfanciaUpdateView,
    IntervencionCentroInfanciaCreateView,
    IntervencionCentroInfanciaDeleteView,
    IntervencionCentroInfanciaDetailView,
    IntervencionCentroInfanciaUpdateView,
    NominaCentroInfanciaCreateView,
    NominaCentroInfanciaDeleteView,
    NominaCentroInfanciaDetailView,
    ObservacionCentroInfanciaCreateView,
    ObservacionCentroInfanciaDeleteView,
    ObservacionCentroInfanciaDetailView,
    ObservacionCentroInfanciaUpdateView,
    centrodeinfancia_ajax,
    eliminar_archivo_intervencion_centrodeinfancia,
    nomina_centrodeinfancia_editar_ajax,
    subir_archivo_intervencion_centrodeinfancia,
)
from centrodeinfancia.views_export import CentroDeInfanciaExportView


urlpatterns = [
    path(
        "centrodeinfancia/listar",
        permissions_any_required(["Centro de Infancia Listar"])(
            CentroDeInfanciaListView.as_view()
        ),
        name="centrodeinfancia",
    ),
    path(
        "centrodeinfancia/exportar",
        permissions_any_required(["Centro de Infancia Listar", "Exportar a csv"])(
            CentroDeInfanciaExportView.as_view()
        ),
        name="centrodeinfancia_exportar",
    ),
    path(
        "centrodeinfancia/crear",
        permissions_any_required(["Centro de Infancia Crear"])(
            CentroDeInfanciaCreateView.as_view()
        ),
        name="centrodeinfancia_crear",
    ),
    path(
        "centrodeinfancia/detalle/<int:pk>",
        permissions_any_required(["Centro de Infancia Ver"])(
            CentroDeInfanciaDetailView.as_view()
        ),
        name="centrodeinfancia_detalle",
    ),
    path(
        "centrodeinfancia/editar/<int:pk>",
        permissions_any_required(["Centro de Infancia Editar"])(
            CentroDeInfanciaUpdateView.as_view()
        ),
        name="centrodeinfancia_editar",
    ),
    path(
        "centrodeinfancia/eliminar/<int:pk>",
        permissions_any_required(["Centro de Infancia Eliminar"])(
            CentroDeInfanciaDeleteView.as_view()
        ),
        name="centrodeinfancia_eliminar",
    ),
    path(
        "centrodeinfancia/ajax/",
        centrodeinfancia_ajax,
        name="centrodeinfancia_ajax",
    ),
    path(
        "centrodeinfancia/<int:pk>/nomina/",
        permissions_any_required(["Centro de Infancia Nomina Ver"])(
            NominaCentroInfanciaDetailView.as_view()
        ),
        name="centrodeinfancia_nomina_ver",
    ),
    path(
        "centrodeinfancia/<int:pk>/nomina/crear/",
        permissions_any_required(["Centro de Infancia Nomina Crear"])(
            NominaCentroInfanciaCreateView.as_view()
        ),
        name="centrodeinfancia_nomina_crear",
    ),
    path(
        "centrodeinfancia/editar-nomina/<int:pk>/",
        permissions_any_required(["Centro de Infancia Nomina Editar"])(
            nomina_centrodeinfancia_editar_ajax
        ),
        name="centrodeinfancia_nomina_editar_ajax",
    ),
    path(
        "centrodeinfancia/<int:pk>/nomina/<int:pk2>/eliminar/",
        permissions_any_required(["Centro de Infancia Nomina Borrar"])(
            NominaCentroInfanciaDeleteView.as_view()
        ),
        name="centrodeinfancia_nomina_borrar",
    ),
    path(
        "centrodeinfancia/intervencion/crear/<int:pk>",
        permissions_any_required(["Centro de Infancia Intervencion Crear"])(
            IntervencionCentroInfanciaCreateView.as_view()
        ),
        name="centrodeinfancia_intervencion_crear",
    ),
    path(
        "centrodeinfancia/intervencion/editar/<int:pk>/<int:pk2>",
        permissions_any_required(["Centro de Infancia Intervencion Editar"])(
            IntervencionCentroInfanciaUpdateView.as_view()
        ),
        name="centrodeinfancia_intervencion_editar",
    ),
    path(
        "centrodeinfancia/intervencion/borrar/<int:pk>/<int:intervencion_id>/",
        permissions_any_required(["Centro de Infancia Intervencion Borrar"])(
            IntervencionCentroInfanciaDeleteView.as_view()
        ),
        name="centrodeinfancia_intervencion_borrar",
    ),
    path(
        "centrodeinfancia/intervencion/detalle/<int:pk>/",
        permissions_any_required(["Centro de Infancia Ver"])(
            IntervencionCentroInfanciaDetailView.as_view()
        ),
        name="centrodeinfancia_intervencion_detalle",
    ),
    path(
        "centrodeinfancia/intervencion/<int:intervencion_id>/documentacion/subir/",
        permissions_any_required(["Centro de Infancia Intervencion Editar"])(
            subir_archivo_intervencion_centrodeinfancia
        ),
        name="centrodeinfancia_subir_archivo_intervencion",
    ),
    path(
        "centrodeinfancia/intervencion/<int:intervencion_id>/documentacion/eliminar/",
        permissions_any_required(["Centro de Infancia Intervencion Borrar"])(
            eliminar_archivo_intervencion_centrodeinfancia
        ),
        name="centrodeinfancia_eliminar_archivo_intervencion",
    ),
    path(
        "centrodeinfancia/<int:pk>/observacion/crear/",
        permissions_any_required(["Centro de Infancia Intervencion Crear"])(
            ObservacionCentroInfanciaCreateView.as_view()
        ),
        name="centrodeinfancia_observacion_crear",
    ),
    path(
        "centrodeinfancia/observacion/<int:pk>/",
        permissions_any_required(["Centro de Infancia Ver"])(
            ObservacionCentroInfanciaDetailView.as_view()
        ),
        name="centrodeinfancia_observacion_detalle",
    ),
    path(
        "centrodeinfancia/observacion/<int:pk>/editar/",
        permissions_any_required(["Centro de Infancia Intervencion Editar"])(
            ObservacionCentroInfanciaUpdateView.as_view()
        ),
        name="centrodeinfancia_observacion_editar",
    ),
    path(
        "centrodeinfancia/observacion/<int:pk>/eliminar/",
        permissions_any_required(["Centro de Infancia Intervencion Borrar"])(
            ObservacionCentroInfanciaDeleteView.as_view()
        ),
        name="centrodeinfancia_observacion_eliminar",
    ),
]
