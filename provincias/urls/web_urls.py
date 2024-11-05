from django.urls import path
from provincias.views.web_views import ProyectoCreateView, ProyectoListView, ProyectoUpdateView, ProyectoDeleteView

urlpatterns = [
    path('proyectos/', ProyectoListView.as_view(), name='proyecto_list'),
    path('proyectos/create/', ProyectoCreateView.as_view(), name='proyecto_create'),
    path('proyectos/<int:pk>/update/', ProyectoUpdateView.as_view(), name='proyecto_update'),
    path('proyectos/<int:pk>/delete/', ProyectoDeleteView.as_view(), name='proyecto_delete'),
]
