from django.urls import path
from acompanamientos import views

urlpatterns = [
    path("acompanamiento/<int:comedor_id>/detalle/", views.detalle_acompanamiento, name="detalle_acompanamiento"),
    path("acompanamiento/", views.lista_comedores_acompanamiento, name="lista_comedores_acompanamiento"),
    
]