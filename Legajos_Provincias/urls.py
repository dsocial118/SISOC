from django.urls import path
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from .views import *


urlpatterns = [
    path('legajos_provincias/listar', login_required(LegajosProvinciasListView.as_view()), name='legajosprovincias_listar'),
    path('provincia/<int:provincia_id>/', ProvinciaDatosView.as_view(), name='get_provincia_nombre'),
    path('legajos_provincias/agregar', login_required(LegajosProvinciasCreateView.as_view()), name='legajosprovincias_crear'),
]