from django.contrib.auth.decorators import login_required
from django.urls import path

from legajosprovincias.views import (
    LegajosProvinciasCreateView,
    LegajosProvinciasDeleteView,
    LegajosProvinciasDetailView,
    LegajosProvinciasListView,
    LegajosProvinciasUpdateView,
)

urlpatterns = [
    path("legajosprovincias", login_required(LegajosProvinciasListView.as_view()), name="legajosprovincias_list"),
    path("legajosprovincias/crear", login_required(LegajosProvinciasCreateView.as_view()), name="legajosprovincias_create"),
    path("legajosprovincias/<int:pk>", login_required(LegajosProvinciasDetailView.as_view()), name="legajosprovincias_detail"),
    path("legajosprovincias/editar/<int:pk>", login_required(LegajosProvinciasUpdateView.as_view()), name="legajosprovincias_update"),
    path("legajosprovincias/eliminar/<int:pk>", login_required(LegajosProvinciasDeleteView.as_view()), name="legajosprovincias_delete"),
]