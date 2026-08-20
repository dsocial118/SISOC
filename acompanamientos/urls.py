from django.urls import path
from acompanamientos import views
from acompanamientos.views_export import AcompanamientoExportView

from core.decorators import permissions_all_required, permissions_any_required

urlpatterns = [
    path(
        "acompanamiento/<int:comedor_id>/detalle/",
        permissions_any_required(["acompanamientos.view_informacionrelevante"])(
            views.AcompanamientoDetailView.as_view()
        ),
        name="detalle_acompanamiento",
    ),
    path(
        "acompanamiento/",
        permissions_any_required(["acompanamientos.view_informacionrelevante"])(
            views.ComedoresAcompanamientoListView.as_view()
        ),
        name="lista_comedores_acompanamiento",
    ),
    path(
        "acompanamiento/exportar/",
        permissions_any_required(["auth.role_exportar_a_csv"])(
            AcompanamientoExportView.as_view()
        ),
        name="lista_comedores_acompanamiento_exportar",
    ),
    path(
        "comedor/<int:comedor_id>/restaurar-hito/",
        permissions_all_required(
            ["auth.role_tecnico_comedor", "acompanamientos.change_hitos"]
        )(views.restaurar_hito),
        name="restaurar_hito",
    ),
    path(
        "acompanamiento/<int:comedor_id>/finalizar/",
        permissions_any_required(["acompanamientos.view_informacionrelevante"])(
            views.finalizar_acompanamiento
        ),
        name="finalizar_acompanamiento",
    ),
    path(
        "acompanamiento/ajax/",
        permissions_any_required(["acompanamientos.view_informacionrelevante"])(
            views.comedores_acompanamiento_ajax
        ),
        name="comedores_acompanamiento_ajax",
    ),
]
