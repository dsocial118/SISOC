from django.urls import path

from centrodefamilia.views.informe_cabal import InformeCabalPreviewView, InformeCabalProcessView, InformeCabalUploadView
from configuraciones.decorators import group_required

from centrodefamilia.views.centro import (
    CentroCreateView,
    CentroDeleteView,
    CentroDetailView,
    CentroListView,
    CentroUpdateView,
)

from centrodefamilia.views.actividad import (
    ActividadCentroCreateView,
    ActividadCentroDetailView,
    ActividadCentroListView,
    ActividadCentroUpdateView,
    ActividadCreateView,
    cargar_actividades_por_categoria,
)


from centrodefamilia.views.participante import (
    ParticipanteActividadCreateView,
    ParticipanteActividadDeleteView,
)


urlpatterns = [

     # Informe Cabal: Upload
path(
        "informe_cabal/",
        group_required(["CDF SSE"])(InformeCabalUploadView.as_view()),
        name="centro_informe_cabal",
    ),
    path(
        "informe_cabal/preview/",
        group_required(["CDF SSE"])(InformeCabalPreviewView.as_view()),
        name="centro_informe_cabal_preview",
    ),
    path(
        "informe_cabal/process/",
        group_required(["CDF SSE"])(InformeCabalProcessView.as_view()),
        name="centro_informe_cabal_process",
    ),

    path(
        "centros/",
        group_required(["ReferenteCentro", "CDF SSE"])(CentroListView.as_view()),
        name="centro_list",
    ),
    path(
        "centros/nuevo/",
        group_required(["ReferenteCentro", "CDF SSE"])(CentroCreateView.as_view()),
        name="centro_create",
    ),
    path(
        "centros/<int:pk>/editar/",
        group_required(["ReferenteCentro", "CDF SSE"])(CentroUpdateView.as_view()),
        name="centro_update",
    ),
    path(
        "centros/<int:pk>/",
        group_required(["ReferenteCentro", "CDF SSE"])(CentroDetailView.as_view()),
        name="centro_detail",
    ),
    path(
        "centros/<int:pk>/eliminar/",
        group_required(["ReferenteCentro", "CDF SSE"])(CentroDeleteView.as_view()),
        name="centro_delete",
    ),
    path(
        "actividades/",
        group_required(["ReferenteCentro", "CDF SSE"])(
            ActividadCentroListView.as_view()
        ),
        name="actividadcentro_list",
    ),
    path(
        "centros/<int:centro_id>/actividades/nueva/",
        group_required(["ReferenteCentro", "CDF SSE"])(
            ActividadCentroCreateView.as_view()
        ),
        name="actividadcentro_create",
    ),
    path(
        "centros/<int:centro_id>/actividades/<int:pk>/detalle/",
        group_required(["ReferenteCentro", "CDF SSE"])(
            ActividadCentroDetailView.as_view()
        ),
        name="actividadcentro_detail",
    ),
    path(
        "centros/<int:centro_id>/actividades/<int:actividad_id>/participantes/crear/",
        group_required(["ReferenteCentro", "CDF SSE"])(
            ParticipanteActividadCreateView.as_view()
        ),
        name="participanteactividad_create",
    ),
    path(
        "centros/<int:centro_id>/actividades/<int:pk>/editar/",
        group_required(["ReferenteCentro", "CDF SSE"])(
            ActividadCentroUpdateView.as_view()
        ),
        name="actividadcentro_edit",
    ),
    path(
        "ajax/actividades/",
        group_required(["ReferenteCentro", "CDF SSE"])(
            cargar_actividades_por_categoria
        ),
        name="ajax_cargar_actividades",
    ),
    path(
        "centros/<int:centro_id>/actividades/<int:actividad_id>/participantes/<int:pk>/eliminar/",
        group_required(["ReferenteCentro", "CDF SSE"])(
            ParticipanteActividadDeleteView.as_view()
        ),
        name="participanteactividad_delete",
    ),
    path(
        "actividades/nueva/",
        group_required(["CDF SSE"])(ActividadCreateView.as_view()),
        name="actividad_create_sola",
    ),
]
