from django.contrib.auth.decorators import login_required
from django.urls import path

from legajosprovincias.views import (
    LegajosProvinciasCreateView,
    LegajosProvinciasDeleteView,
    LegajosProvinciasDetailView,
    LegajosProvinciasListView,
    LegajosProvinciasUpdateView,
    LegajosProvinciasProyectosListView,
    LegajosProvinciasProyectosDetailView,
    LegajosProvinciasPresupuestoListView,
    LegajosProvinciasPresupuestoDetailView,
    LegajosProvinciasPresupuestoUpdateView,
    LegajosProvinciasPresupuestoDeleteView,
    LegajosProvinciasPresupuestoHistorialView,
    
)

urlpatterns = [
    path("legajosprovincias", login_required(LegajosProvinciasListView.as_view()), name="legajosprovincias_listar"),
    path("legajosprovincias/crear", login_required(LegajosProvinciasCreateView.as_view()), name="legajosprovincias_crear"),
    path("legajosprovincias/detalle/<int:pk>", login_required(LegajosProvinciasDetailView.as_view()), name="legajosprovincias_detalle"),
    path("legajosprovincias/editar/<int:pk>", login_required(LegajosProvinciasUpdateView.as_view()), name="legajosprovincias_editar"),
    path("legajosprovincias/eliminar/<int:pk>", login_required(LegajosProvinciasDeleteView.as_view()), name="legajosprovincias_borrar"),
    path("legajosprovincias/proyectos/<int:pk>", login_required(LegajosProvinciasProyectosListView.as_view()), name="legajosprovincias_proyectos_listar"),
    path("legajosprovincias/proyectos/detalle/<int:pk>", login_required(LegajosProvinciasProyectosDetailView.as_view()), name="legajosprovincias_proyectos_detalle"),
    path("legajosprovincias/presupuesto/listar/<int:pk>", login_required(LegajosProvinciasPresupuestoListView.as_view()), name="legajosprovincias_presupuesto_listar"), 
    path("legajosprovincias/presupuesto/detalle/<int:pk>", login_required(LegajosProvinciasPresupuestoDetailView.as_view()), name="legajosprovincias_presupuesto_detalle"),
    path("legajosprovincias/presupuesto/editar/<int:pk>", login_required(LegajosProvinciasPresupuestoUpdateView.as_view()), name="legajosprovincias_presupuesto_editar"),
    path("legajosprovincias/presupuesto/borrar/<int:pk>", login_required(LegajosProvinciasPresupuestoDeleteView.as_view()), name="legajosprovincias_presupuesto_borrar"),
    path("legajosprovincias/presupuesto/historial/<int:pk>", login_required(LegajosProvinciasPresupuestoHistorialView.as_view()), name="legajosprovincias_presupuesto_historial"),
]