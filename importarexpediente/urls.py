from django.urls import path
from .views import (
    ImportExpedientesView,
    ImportarExpedienteListView,
    ImportarExpedienteDetalleListView,
    ImportDatosView,
    BorrarDatosImportadosView,
)

urlpatterns = [
    path("importarexpedientes/upload", ImportExpedientesView.as_view(), name="upload"),
    path(
        "importarexpedientes/listar",
        ImportarExpedienteListView.as_view(),
        name="importarexpedientes_list",
    ),
    path(
        "importarexpedientes/<int:id_archivo>/",
        ImportarExpedienteDetalleListView.as_view(),
        name="importarexpediente_detail",
    ),
    path(
        "importarexpedientes/<int:id_archivo>/importar_datos/",
        ImportDatosView.as_view(),
        name="importar_datos",
    ),
    path(
        "importarexpedientes/<int:id_archivo>/borrar_datos_importados/",
        BorrarDatosImportadosView.as_view(),
        name="borrar_datos_importados",
    ),
]
