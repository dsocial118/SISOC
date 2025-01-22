# urls.py
from django.urls import path
from .views import CentroDesarrolloInfantilListView

urlpatterns = [
    path(
        "centros-desarrollo-infantil/",
        CentroDesarrolloInfantilListView.as_view(),
        name="centrodesarrolloinfantil_listar",
    ),
]
