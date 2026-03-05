from django.urls import path
from acompanamientos import views
from acompanamientos.views_export import AcompanamientoExportView

from core.decorators import permissions_any_required

urlpatterns = [
    path(
        "acompanamiento/<int:comedor_id>/detalle/",
        permissions_any_required(
            [
                "Acompanamiento Detalle",
                "Area Legales",
                "Tecnico Comedor",
                "Coordinador Equipo Tecnico",
            ]
        )(views.AcompanamientoDetailView.as_view()),
        name="detalle_acompanamiento",
    ),
    path(
        "acompanamiento/",
        permissions_any_required(
            [
                "Acompanamiento Listar",
                "Area Legales",
                "Tecnico Comedor",
                "Coordinador Equipo Tecnico",
            ]
        )(views.ComedoresAcompanamientoListView.as_view()),
        name="lista_comedores_acompanamiento",
    ),
    path(
        "acompanamiento/exportar/",
        permissions_any_required(["Exportar a csv"])(AcompanamientoExportView.as_view()),
        name="lista_comedores_acompanamiento_exportar",
    ),
    path(
        "comedor/<int:comedor_id>/restaurar-hito/",
        permissions_any_required(["Tecnico Comedor", "Coordinador Equipo Tecnico"])(
            views.restaurar_hito
        ),
        name="restaurar_hito",
    ),
    path(
        "acompanamiento/ajax/",
        permissions_any_required(
            [
                "Acompanamiento Listar",
                "Area Legales",
                "Tecnico Comedor",
                "Coordinador Equipo Tecnico",
            ]
        )(views.comedores_acompanamiento_ajax),
        name="comedores_acompanamiento_ajax",
    ),
]
