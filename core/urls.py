from django.urls import path

from .views import (
    inicio_view,
    load_localidad,
    load_municipios,
)

urlpatterns = [
    path("inicio/", inicio_view, name="inicio"),
    path("ajax/load-municipios/", load_municipios, name="ajax_load_municipios"),
    path("ajax/load-localidades/", load_localidad, name="ajax_load_localidades"),
]
