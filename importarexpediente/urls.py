from django.urls import path
from .views import ImportExpedientesView

app_name = "importarexpedientes"

urlpatterns = [
    path("", ImportExpedientesView.as_view(), name="upload"),
]