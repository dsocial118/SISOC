from django.contrib.auth.decorators import login_required
from django.urls import path

from .views import (
    load_asentamiento,
    load_departamento,
    load_localidad,
    load_municipios,
)

urlpatterns = [
    path("ajax/load-municipios/", load_municipios, name="ajax_load_municipios"),
    path("ajax/load-localidades/", load_localidad, name="ajax_load_localidades"),
    path("ajax/load-departamentos/", load_departamento, name="ajax_load_departamentos"),
    path("ajax/load-asentamientos/", load_asentamiento, name="ajax_load_asentamientos"),
]
