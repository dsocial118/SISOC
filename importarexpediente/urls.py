from django.urls import path
from core.decorators import permissions_any_required
from .views import (
    ImportExpedientesView,
    ImportarExpedienteListView,
    ImportarExpedienteDetalleListView,
    ImportarFechasAcreditacionView,
    importarexpedientes_ajax,
    importarexpediente_detail_ajax,
    ImportDatosView,
    BorrarDatosImportadosView,
    descargar_archivo_importado,
)

urlpatterns = [
    path("importarexpedientes/upload", ImportExpedientesView.as_view(), name="upload"),
    path(
        "importarexpedientes/listar",
        ImportarExpedienteListView.as_view(),
        name="importarexpedientes_list",
    ),
    path(
        "importarexpedientes/ajax/",
        importarexpedientes_ajax,
        name="importarexpedientes_ajax",
    ),
    path(
        "importarexpedientes/<int:id_archivo>/",
        ImportarExpedienteDetalleListView.as_view(),
        name="importarexpediente_detail",
    ),
    path(
        "importarexpedientes/<int:id_archivo>/descargar/",
        descargar_archivo_importado,
        name="descargar_archivo_importado",
    ),
    path(
        "importarexpedientes/<int:id_archivo>/ajax/",
        importarexpediente_detail_ajax,
        name="importarexpediente_detail_ajax",
    ),
    path(
        "importarexpedientes/<int:id_archivo>/fechas-acreditacion/",
        permissions_any_required(
            [
                "importarexpediente.change_archivosimportados",
                "expedientespagos.change_expedientepago",
            ]
        )(ImportarFechasAcreditacionView.as_view()),
        name="importar_fechas_acreditacion",
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
