# centrodefamilia/urls.py
from django.urls import path
from configuraciones.decorators import group_required

from centrodefamilia.views.informecabal import (
    InformeCabalArchivoDetailView,
    InformeCabalListView,
    InformeCabalPreviewAjaxView,
    InformeCabalProcessAjaxView,
    InformeCabalRegistroDetailView,
    InformeCabalReprocessCenterAjaxView,
)

from centrodefamilia.views.centro import (
    CentroCreateView,
    CentroDeleteView,
    CentroDetailView,
    CentroListView,
    CentroUpdateView,
    InformeCabalArchivoPorCentroDetailView,
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
    ParticipanteActividadListEsperaView,
    ParticipanteActividadPromoverView,
)

urlpatterns = [
    path(
        "centros/<int:centro_id>/informecabal/<int:pk>/",
        group_required(["CDF SSE"])(InformeCabalArchivoPorCentroDetailView.as_view()),
        name="informecabal_archivo_centro_detail",
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
        "centros/<int:centro_id>/actividades/<int:actividad_id>/lista-espera/",
        group_required(["ReferenteCentro", "CDF SSE"])(
            ParticipanteActividadListEsperaView.as_view()
        ),
        name="actividadcentro_lista_espera",
    ),
    path(
        "centros/<int:centro_id>/actividades/<int:actividad_id>/lista-espera/<int:pk>/promover/",
        group_required(["ReferenteCentro", "CDF SSE"])(
            ParticipanteActividadPromoverView.as_view()
        ),
        name="participanteactividad_promover",
    ),
    # ——— NUEVO: Informe CABAL ———
    path(
        "informecabal/",
        group_required(["CDF SSE"])(InformeCabalListView.as_view()),
        name="informecabal_list",
    ),
    path(
        "informecabal/preview/",
        group_required(["CDF SSE"])(InformeCabalPreviewAjaxView.as_view()),
        name="informecabal_preview",
    ),
    path(
        "informecabal/<int:pk>/",
        group_required(["CDF SSE"])(InformeCabalArchivoDetailView.as_view()),
        name="informecabal_archivo_detail",
    ),
    path(
        "informecabal/process/",
        group_required(["CDF SSE"])(InformeCabalProcessAjaxView.as_view()),
        name="informecabal_process",
    ),
    path(
        "informecabal/registro/<int:pk>/",
        group_required(["CDF SSE"])(InformeCabalRegistroDetailView.as_view()),
        name="informecabal_registro_detail",
    ),
    # (Dejamos tus rutas previas de “expedientes” intactas, aunque NO se usan en este flujo)
    path(
        "actividades/nueva/",
        group_required(["CDF SSE"])(ActividadCreateView.as_view()),
        name="actividad_create_sola",
    ),
    # repro
    path(
        "informecabal/reprocess/",
        group_required(["CDF SSE"])(InformeCabalReprocessCenterAjaxView.as_view()),
        name="informecabal_reprocess_center",
    ),
]
