from django.urls import path
from .views import ImportExpedientesView, ImportarExpedienteListView, ImportarExpedienteDeleteView, ImportarExpedienteDetailView

urlpatterns = [
    path("importarexpedientes/upload", ImportExpedientesView.as_view(), name="upload"),
    path("importarexpedientes/", ImportarExpedienteListView.as_view(), name="importarexpedientes_list"),
    path("importarexpedientes/<int:pk>/delete", ImportarExpedienteDeleteView.as_view(), name="importarexpediente_delete"),
    path("importarexpedientes/<int:pk>/", ImportarExpedienteDetailView.as_view(), name="importarexpediente_detail"),
]