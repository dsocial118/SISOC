from django.urls import path
from acompanamientos import views

from core.decorators import permissions_any_required

urlpatterns = [
    path(
        "acompanamiento/<int:comedor_id>/detalle/",
        permissions_any_required(
            [
                "acompanamientos.view_informacionrelevante",
                "comedores.view_comedor",
                "admisiones.view_admision",
                "expedientespagos.view_expedientepago",
            ]
        )(views.AcompanamientoUnavailableView.as_view()),
        name="detalle_acompanamiento",
    ),
    path(
        "acompanamiento/",
        permissions_any_required(
            [
                "acompanamientos.view_informacionrelevante",
                "comedores.view_comedor",
                "admisiones.view_admision",
                "expedientespagos.view_expedientepago",
            ]
        )(views.AcompanamientoUnavailableView.as_view()),
        name="lista_comedores_acompanamiento",
    ),
    path(
        "acompanamiento/exportar/",
        permissions_any_required(["auth.role_exportar_a_csv"])(views.acompanamiento_unavailable),
        name="lista_comedores_acompanamiento_exportar",
    ),
    path(
        "comedor/<int:comedor_id>/restaurar-hito/",
        permissions_any_required(
            [
                "comedores.view_comedor",
                "admisiones.view_admision",
                "acompanamientos.view_informacionrelevante",
            ]
        )(views.acompanamiento_unavailable),
        name="restaurar_hito",
    ),
    path(
        "acompanamiento/ajax/",
        permissions_any_required(
            [
                "acompanamientos.view_informacionrelevante",
                "comedores.view_comedor",
                "admisiones.view_admision",
                "expedientespagos.view_expedientepago",
            ]
        )(views.acompanamiento_unavailable),
        name="comedores_acompanamiento_ajax",
    ),
]
