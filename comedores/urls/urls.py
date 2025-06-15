from django.urls import path

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
    NominaUpdateView,
    AsignarDuplaListView,
)

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
from configuraciones.decorators import group_required
from rendicioncuentasfinal.views import (
    DocumentosRendicionCuentasFinalListView,
    RendicionCuentasFinalDetailView,
    adjuntar_documento_rendicion_cuenta_final,
    crear_documento_rendicion_cuentas_final,
    eliminar_documento_rendicion_cuentas_final,
    subsanar_documento_rendicion_cuentas_final,
    validar_documento_rendicion_cuentas_final,
)

urlpatterns = [
    path(
        "comedores/listar",
        group_required(["Comedores Listar", "Tecnico Comedor", "Abogado Dupla"])(
            ComedorListView.as_view()
        ),
        name="comedores",
    ),
    path(
        "comedores/crear",
        group_required(["Comedores Crear"])(ComedorCreateView.as_view()),
        name="comedor_crear",
    ),
    path(
        "comedores/<pk>",
        group_required(["Comedores Ver", "Tecnico Comedor", "Abogado Dupla"])(
            ComedorDetailView.as_view()
        ),
        name="comedor_detalle",
    ),
    path(
        "comedores/<pk>/editar",
        group_required(["Comedores Editar"])(ComedorUpdateView.as_view()),
        name="comedor_editar",
    ),
    path(
        "comedores/<pk>/eliminar",
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
        "comedores/<comedor_pk>/observacion/<pk>",
        group_required(["Comedores Observaciones Detalle"])(
            ObservacionDetailView.as_view()
        ),
        name="observacion_detalle",
    ),
    path(
        "comedores/<comedor_pk>/observacion/<pk>/editar",
        group_required(["Comedores Observaciones Editar"])(
            ObservacionUpdateView.as_view()
        ),
        name="observacion_editar",
    ),
    path(
        "comedores/<comedor_pk>/observacion/<pk>/eliminar",
        group_required(["Comedores Observaciones Eliminar"])(
            ObservacionDeleteView.as_view()
        ),
        name="observacion_eliminar",
    ),
    path(
        "comedores/intervencion/ver/<pk>",
        group_required(["Comedores Intervencion Ver"])(
            IntervencionDetailView.as_view()
        ),
        name="comedor_intervencion_ver",
    ),
    path(
        "comedores/nomina/ver/<pk>",
        group_required(["Comedores Nomina Ver"])(NominaDetailView.as_view()),
        name="nomina_ver",
    ),
    path(
        "comedores/nomina/crear/<pk>",
        group_required(["Comedores Nomina Crear"])(NominaCreateView.as_view()),
        name="nomina_crear",
    ),
    path(
        "comedores/intervencion/crear/<pk>",
        group_required(["Comedores Intervencion Crear"])(
            IntervencionCreateView.as_view()
        ),
        name="comedor_intervencion_crear",
    ),
    path(
        "comedores/intervencion/editar/<pk>/<pk2>",
        group_required(["Comedores Intervencion Editar"])(
            IntervencionUpdateView.as_view()
        ),
        name="comedores_intervencion_editar",
    ),
    path(
        "comedores/nomina/editar/<pk>/<pk2>",
        group_required(["Comedores Nomina Editar"])(NominaUpdateView.as_view()),
        name="nomina_editar",
    ),
    path(
        "comedores/intervencion/borrar/<int:comedor_id>/<int:intervencion_id>/",
        group_required(["Comedores Nomina Borrar"])(IntervencionDeleteView.as_view()),
        name="comedor_intervencion_borrar",
    ),
    path(
        "comedores/nomina/borrar/<pk>/<pk2>",
        group_required(["Comedores Nomina Borrar"])(NominaDeleteView.as_view()),
        name="nomina_borrar",
    ),
    path(
        "comedores/dupla/asignar/<pk>",
        group_required(["Comedores Dupla Asignar"])(AsignarDuplaListView.as_view()),
        name="dupla_asignar",
    ),
    path(
        "comedores/ajax/load-subestadosintervenciones/",
        sub_estados_intervenciones_ajax,
        name="ajax_load_subestadosintervenciones",
    ),
    path(
        "intervencion/<int:intervencion_id>/documentacion/subir/",
        subir_archivo_intervencion,
        name="subir_archivo_intervencion",
    ),
    path(
        "intervencion/<int:intervencion_id>/documentacion/eliminar/",
        eliminar_archivo_intervencion,
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
        "comedores/<pk>/rendicion_cuentas_final",
        group_required("Tecnico Comedor")(RendicionCuentasFinalDetailView.as_view()),
        name="rendicion_cuentas_final",
    ),
    path(
        "rendicion_cuentas_final/documento/adjuntar/",
        adjuntar_documento_rendicion_cuenta_final,
        name="adjuntar_documento_rendicion_cuenta_final",
    ),
    path(
        "rendicion_cuentas_final/<int:rendicion_id>/crear/",
        crear_documento_rendicion_cuentas_final,
        name="crear_documento_rendicion_cuentas_final",
    ),
    path(
        "rendicion_cuentas_final/<int:rendicion_id>/fisicamente_presentada/",
        switch_rendicion_final_fisicamente_presentada,
        name="switch_rendicion_final_fisicamente_presentada",
    ),
    path(
        "rendicion_cuentas_final/documento/<int:documento_id>/eliminar/",
        eliminar_documento_rendicion_cuentas_final,
        name="eliminar_documento_rendicion_cuentas_final",
    ),
    path(
        "rendicion_cuentas_final/documento/<int:documento_id>/validar/",
        validar_documento_rendicion_cuentas_final,
        name="validar_documento_rendicion_cuentas_final",
    ),
    path(
        "rendicion_cuentas_final/documento/<int:documento_id>/subsanar/",
        subsanar_documento_rendicion_cuentas_final,
        name="subsanar_documento_rendicion_cuentas_final",
    ),
    path(
        "rendicion_cuentas_final/listar/",
        group_required(["Area Contable", "Area Legales"])(
            DocumentosRendicionCuentasFinalListView.as_view()
        ),
        name="rendicion_cuentas_final_listar",
    ),
]
