from django.urls import path

from core.decorators import group_required
from rendicioncuentasfinal.views import (
    DocumentosRendicionCuentasFinalListView,
    RendicionCuentasFinalDetailView,
    adjuntar_documento_rendicion_cuenta_final,
    crear_documento_rendicion_cuentas_final,
    eliminar_documento_rendicion_cuentas_final,
    subsanar_documento_rendicion_cuentas_final,
    validar_documento_rendicion_cuentas_final,
    switch_rendicion_final_fisicamente_presentada,
    documentos_rendicion_cuentas_final_ajax,
)

urlpatterns = [
    path(
        "comedores/<int:pk>/rendicion_cuentas_final/",
        group_required(["Tecnico Comedor", "Coordinador Equipo Tecnico"])(
            RendicionCuentasFinalDetailView.as_view()
        ),
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
        group_required(
            [
                "Area Contable",
                "Area Legales",
                "Tecnico Comedor",
                "Coordinador Equipo Tecnico",
            ]
        )(DocumentosRendicionCuentasFinalListView.as_view()),
        name="rendicion_cuentas_final_listar",
    ),
    # AJAX endpoint
    path(
        # TODO: Migrar a router DRF (estilo centrodefamilia).
        "rendicion_cuentas_final/ajax/",
        documentos_rendicion_cuentas_final_ajax,
        name="documentos_rendicion_cuentas_final_ajax",
    ),
]
