from django.urls import path
from acompanamientos import views
from core.decorators import group_required

urlpatterns = [
    path(
        "acompanamiento/<int:comedor_id>/detalle/",
        group_required(["Acompanamiento Detalle", "Area Legales", "Tecnico Comedor"])(
            views.AcompanamientoDetailView.as_view()
        ),
        name="detalle_acompanamiento",
    ),
    path(
        "acompanamiento/",
        group_required(["Acompanamiento Listar", "Area Legales", "Tecnico Comedor"])(
            views.ComedoresAcompanamientoListView.as_view()
        ),
        name="lista_comedores_acompanamiento",
    ),
    path(
        "comedor/<int:comedor_id>/restaurar-hito/",
        views.restaurar_hito,
        name="restaurar_hito",
    ),
]
