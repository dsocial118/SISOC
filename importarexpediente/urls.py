from django.urls import path
from .views import ImportExpedientesView, ImportarExpedienteListView, ImportarExpedienteDetalleListView

urlpatterns = [
    path("importarexpedientes/upload", ImportExpedientesView.as_view(), name="upload"),
    path("importarexpedientes/listar", ImportarExpedienteListView.as_view(), name="importarexpedientes_list"),
    path("importarexpedientes/<int:id_archivo>/", ImportarExpedienteDetalleListView.as_view(), name="importarexpediente_detail"),
]