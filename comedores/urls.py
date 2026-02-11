from django.urls import path
from django.contrib.auth.decorators import login_required
from comedores.views import (
    ComedorCreateView,
    ComedorDeleteView,
    ComedorDetailView,
    ComedorListView,
    ComedorUpdateView,
    ObservacionCreateView,
    ObservacionDeleteView,
    ObservacionDetailView,
    ObservacionUpdateView,
    NominaDetailView,
    NominaCreateView,
    NominaDeleteView,
    AsignarDuplaListView,
    relevamiento_crear_editar_ajax,
    nomina_editar_ajax,
    validar_comedor,
)
from comedores.views.export import ComedorExportView


from comedores.views_territorial import (
    obtener_territoriales_api,
    sincronizar_territoriales_api,
    estadisticas_cache_territoriales,
)

# Views de prueba eliminadas

from intervenciones.views import (
    sub_estados_intervenciones_ajax,
    IntervencionCreateView,
    IntervencionUpdateView,
    IntervencionDeleteView,
    subir_archivo_intervencion,
    eliminar_archivo_intervencion,
    IntervencionDetailIndividualView,
    IntervencionDetailView,
)
from core.decorators import group_required

urlpatterns = [
    path(
        "comedores/listar",
        group_required(
            [
                "Comedores Listar",
                "Tecnico Comedor",
                "Abogado Dupla",
                "Coordinador Equipo Tecnico",
                "Coordinador general",
            ]
        )(ComedorListView.as_view()),
        name="comedores",
    ),
    path(
        "comedores/exportar",
        group_required(
            [
                "Exportar a csv",
                "Administrador",
            ]
        )(ComedorExportView.as_view()),
        name="comedor_export",
    ),
    path(
        "comedores/crear",
        group_required(["Comedores Crear"])(ComedorCreateView.as_view()),
        name="comedor_crear",
    ),
    path(
        "comedores/<int:pk>",
        group_required(
            [
                "Comedores Ver",
                "Tecnico Comedor",
                "Abogado Dupla",
                "Coordinador Equipo Tecnico",
                "Coordinador general",
            ]
        )(ComedorDetailView.as_view()),
        name="comedor_detalle",
    ),
    path(
        "comedores/<int:pk>/editar",
        group_required(["Comedores Editar"])(ComedorUpdateView.as_view()),
        name="comedor_editar",
    ),
    path(
        "comedores/<int:pk>/eliminar",
        group_required(["Comedores Eliminar"])(ComedorDeleteView.as_view()),
        name="comedor_eliminar",
    ),
    path(
        "comedores/<comedor_pk>/observacion/crear",
        group_required(["Comedores Observaciones Crear"])(
            ObservacionCreateView.as_view()
        ),
        name="observacion_crear",
    ),
    path(
        "comedores/observacion/<int:pk>",
        group_required(["Comedores Observaciones Detalle"])(
            ObservacionDetailView.as_view()
        ),
        name="observacion_detalle",
    ),
    path(
        "comedores/observacion/<int:pk>/editar",
        group_required(["Comedores Observaciones Editar"])(
            ObservacionUpdateView.as_view()
        ),
        name="observacion_editar",
    ),
    path(
        "comedores/observacion/<int:pk>/eliminar",
        group_required(["Comedores Observaciones Eliminar"])(
            ObservacionDeleteView.as_view()
        ),
        name="observacion_eliminar",
    ),
    path(
        "comedores/intervencion/ver/<int:pk>",
        group_required(["Comedores Intervencion Ver"])(
            IntervencionDetailView.as_view()
        ),
        name="comedor_intervencion_ver",
    ),
    path(
        "comedores/intervencion/crear/<int:pk>",
        group_required(["Comedores Intervencion Crear"])(
            IntervencionCreateView.as_view()
        ),
        name="comedor_intervencion_crear",
    ),
    path(
        "comedores/intervencion/editar/<int:pk>/<int:pk2>",
        group_required(["Comedores Intervencion Editar"])(
            IntervencionUpdateView.as_view()
        ),
        name="comedores_intervencion_editar",
    ),
    path(
        "comedores/intervencion/borrar/<int:comedor_id>/<int:intervencion_id>/",
        group_required(["Comedores Nomina Borrar"])(IntervencionDeleteView.as_view()),
        name="comedor_intervencion_borrar",
    ),
    path(
        "comedores/dupla/asignar/<int:pk>",
        group_required(["Comedores Dupla Asignar"])(AsignarDuplaListView.as_view()),
        name="dupla_asignar",
    ),
    path(
        "comedores/ajax/load-subestadosintervenciones/",
        login_required(sub_estados_intervenciones_ajax),
        name="ajax_load_subestadosintervenciones",
    ),
    path(
        # TODO: Migrar a router DRF (estilo centrodefamilia).
        "intervencion/<int:intervencion_id>/documentacion/subir/",
        group_required(["Tecnico Comedor"])(subir_archivo_intervencion),
        name="subir_archivo_intervencion",
    ),
    path(
        # TODO: Migrar a router DRF (estilo centrodefamilia).
        "intervencion/<int:intervencion_id>/documentacion/eliminar/",
        group_required(["Tecnico Comedor"])(eliminar_archivo_intervencion),
        name="eliminar_archivo_intervencion",
    ),
    path(
        "intervencion/detalle/<int:pk>/",
        group_required(["Comedores Intervenciones Detalle"])(
            IntervencionDetailIndividualView.as_view()
        ),
        name="intervencion_detalle",
    ),
    path(
        "comedores/<int:pk>/nomina/",
        group_required(["Comedores Nomina Ver"])(NominaDetailView.as_view()),
        name="nomina_ver",
    ),
    path(
        "comedores/editar-nomina/<int:pk>/",
        group_required(["Comedores Nomina Editar"])(nomina_editar_ajax),
        name="nomina_editar_ajax",
    ),
    path(
        "comedores/<int:pk>/nomina/crear/",
        group_required(["Comedores Nomina Crear"])(NominaCreateView.as_view()),
        name="nomina_crear",
    ),
    path(
        "comedores/<int:pk>/nomina/<int:pk2>/eliminar/",
        group_required(["Comedores Nomina Borrar"])(NominaDeleteView.as_view()),
        name="nomina_borrar",
    ),
    path(
        "comedores/ajax/<int:pk>/relevamiento/",
        relevamiento_crear_editar_ajax,
        name="relevamiento_create_edit_ajax",
    ),
    # esto es prueba de nuevo front para el comedor
    path(
        "comedores_nuevo/<int:pk>",
        group_required(
            [
                "Comedores Ver",
                "Tecnico Comedor",
                "Abogado Dupla",
                "Coordinador Equipo Tecnico",
                "Coordinador general",
            ]
        )(ComedorDetailView.as_view(template_name="comedor/new_comedor_detail.html")),
        name="nuevo_comedor_detalle",
    ),
    path(
        "comedores/<int:comedor_id>/territoriales/",
        obtener_territoriales_api,
        name="api_obtener_territoriales",
    ),
    path(
        "comedores/<int:comedor_id>/territoriales/sincronizar/",
        sincronizar_territoriales_api,
        name="api_sincronizar_territoriales",
    ),
    path(
        "comedores/territoriales/estadisticas/",
        estadisticas_cache_territoriales,
        name="api_estadisticas_territoriales",
    ),
    path(
        "comedores/<int:pk>/validar/",
        login_required(validar_comedor),
        name="validar_comedor",
    ),
]
