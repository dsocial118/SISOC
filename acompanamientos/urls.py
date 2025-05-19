from django.urls import path
from acompanamientos import views

urlpatterns = [
    path(
        "acompanamiento/<int:comedor_id>/detalle/",
        views.AcompanamientoDetailView.as_view(),
        name="detalle_acompanamiento",
    ),
    path(
        "acompanamiento/",
        views.ComedoresAcompanamientoListView.as_view(),
        name="lista_comedores_acompanamiento",
    ),
]
