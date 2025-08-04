from django.urls import path

from configuraciones.decorators import group_required

from centrodefamilia.views.informecabal import (
    ExpedienteCreateView,
    ExpedienteDetailView,
    ExpedienteListView,
    ExpedienteUpdateView,
)

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
    ParticipanteActividadListEsperaView,
    ParticipanteActividadPromoverView,
)

urlpatterns = [
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
    # Lista de espera de participantes
    path(
        "centros/<int:centro_id>/actividades/<int:actividad_id>/lista-espera/",
        group_required(["ReferenteCentro", "CDF SSE"])(
            ParticipanteActividadListEsperaView.as_view()
        ),
        name="actividadcentro_lista_espera",
    ),
    # Promover participante de lista de espera
    path(
        "centros/<int:centro_id>/actividades/<int:actividad_id>/lista-espera/<int:pk>/promover/",
        group_required(["ReferenteCentro", "CDF SSE"])(
            ParticipanteActividadPromoverView.as_view()
        ),
        name="participanteactividad_promover",
    ),
    path(
        "centro/<int:centro_id>/expedientes/",
        group_required(["ReferenteCentro", "CDF SSE"])(ExpedienteListView.as_view()),
        name="expediente_list",
    ),
    path(
        "centro/<int:centro_id>/expedientes/nuevo/",
        group_required(["ReferenteCentro", "CDF SSE"])(ExpedienteCreateView.as_view()),
        name="expediente_create",
    ),
    path(
        "centro/<int:centro_id>/expedientes/<int:pk>/",
        group_required(["ReferenteCentro", "CDF SSE"])(ExpedienteDetailView.as_view()),
        name="expediente_detail",
    ),
    path(
        "centro/<int:centro_id>/expedientes/<int:pk>/editar/",
        group_required(["ReferenteCentro", "CDF SSE"])(ExpedienteUpdateView.as_view()),
        name="expediente_update",
    ),
    path(
        "actividades/nueva/",
        group_required(["CDF SSE"])(ActividadCreateView.as_view()),
        name="actividad_create_sola",
    ),
]
