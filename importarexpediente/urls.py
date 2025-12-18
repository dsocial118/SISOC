from django.urls import path
from .views import ImportExpedientesView

urlpatterns = [
    path("importarexpedientes/upload", ImportExpedientesView.as_view(), name="upload"),
]