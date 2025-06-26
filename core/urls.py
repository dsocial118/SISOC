from django.urls import path

from .views import (
    load_localidad,
    load_municipios,
)

urlpatterns = [
    path("ajax/load-municipios/", load_municipios, name="ajax_load_municipios"),
    path("ajax/load-localidades/", load_localidad, name="ajax_load_localidades"),
]
