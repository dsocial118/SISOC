from django.urls import path

from core.decorators import permissions_any_required
from pas.views import (
    PasDDJJConfirmacionView,
    PasDDJJDownloadView,
    PasDDJJFormularioView,
    PasDDJJMunicipiosView,
    PasDDJJPrivateMediaView,
    PasTitularesImportView,
    PasTokensExportView,
)


urlpatterns = [
    path(
        "media/pas/ddjj/<path:path>",
        PasDDJJPrivateMediaView.as_view(),
        name="pas_ddjj_media_privado",
    ),
    path(
        "pas/ddjj/formulario/<uuid:token>",
        PasDDJJFormularioView.as_view(),
        name="pas_ddjj_formulario",
    ),
    path(
        "pas/ddjj/formulario/<uuid:token>/municipios",
        PasDDJJMunicipiosView.as_view(),
        name="pas_ddjj_municipios",
    ),
    path(
        "pas/ddjj/confirmacion",
        PasDDJJConfirmacionView.as_view(),
        name="pas_ddjj_confirmacion",
    ),
    path(
        "pas/ddjj/<int:pk>/descargar",
        permissions_any_required(["pas.view_paspersona"])(
            PasDDJJDownloadView.as_view()
        ),
        name="pas_ddjj_descargar",
    ),
    path(
        "pas/titulares/importar",
        permissions_any_required(["pas.add_paspersona"])(
            PasTitularesImportView.as_view()
        ),
        name="pas_titulares_importar",
    ),
    path(
        "pas/ddjj/tokens/exportar",
        permissions_any_required(["pas.export_ddjj_tokens"])(
            PasTokensExportView.as_view()
        ),
        name="pas_tokens_exportar",
    ),
]
