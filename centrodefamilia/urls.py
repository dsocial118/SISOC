from django.urls import path

from configuraciones.decorators import group_required

from centrodefamilia.views.centro import (
    CentroDeleteView,
    CentroListView,
    CentroCreateView,
    CentroUpdateView,
    CentroDetailView,
)
from centrodefamilia.views.actividad import (
    ActividadCentroDetailView,
    ActividadCentroListView,
    ActividadCentroCreateView,
    ActividadCentroUpdateView,
    cargar_actividades_por_categoria,
)
from centrodefamilia.views.orientador import (
    OrientadorListView,
    OrientadorCreateView,
    OrientadorUpdateView,
    OrientadorDeleteView,
)
from centrodefamilia.views.participante import ParticipanteActividadCreateView  


urlpatterns = [
    path(
        "centros/",
        group_required(["ReferenteCentro"])(CentroListView.as_view()),
        name="centro_list",
    ),
    path(
        "centros/nuevo/",
        group_required(["ReferenteCentro"])(CentroCreateView.as_view()),
        name="centro_create",
    ),
    path(
        "centros/<int:pk>/editar/",
        group_required(["ReferenteCentro"])(CentroUpdateView.as_view()),
        name="centro_update",
    ),
    path(
        "centros/<int:pk>/",
        group_required(["ReferenteCentro"])(CentroDetailView.as_view()),
        name="centro_detail",
    ),
    path(
        "centros/<int:pk>/eliminar/",
        group_required(["ReferenteCentro"])(CentroDeleteView.as_view()),
        name="centro_delete",
    ),
    path(
        "actividades/",
        group_required(["ReferenteCentro"])(ActividadCentroListView.as_view()),
        name="actividadcentro_list",
    ),
    path(
        "actividades/nueva/",
        group_required(["ReferenteCentro"])(ActividadCentroCreateView.as_view()),
        name="actividadcentro_create",
    ),
    path(
        "centros/<int:centro_id>/actividades/nueva/",
        group_required(["ReferenteCentro"])(ActividadCentroCreateView.as_view()),
        name="actividadcentro_create",
    ),
    path(
        "centros/<int:centro_id>/actividades/<int:pk>/detalle/",
        group_required(["ReferenteCentro"])(ActividadCentroDetailView.as_view()),
        name="actividadcentro_detail",
    ),
    path(
        "centros/<int:centro_id>/actividades/<int:actividad_id>/participantes/crear/",
        group_required(["ReferenteCentro"])(ParticipanteActividadCreateView.as_view()),
        name="participanteactividad_create",
    ),
    path(
        "centros/<int:centro_id>/actividades/<int:pk>/editar/",
        group_required(["superadmin", "ReferenteCentro"])(
            ActividadCentroUpdateView.as_view()
        ),
        name="actividadcentro_edit",
    ),
    path(
        "ajax/actividades/",
        cargar_actividades_por_categoria,
        name="ajax_cargar_actividades",
    ),
    path(
        "centros/<int:centro_id>/orientadores/",
        OrientadorListView.as_view(),
        name="orientador_list",
    ),
    path(
        "centros/<int:centro_id>/orientadores/nuevo/",
        OrientadorCreateView.as_view(),
        name="orientador_create",
    ),
    path(
        "orientadores/<int:pk>/editar/",
        OrientadorUpdateView.as_view(),
        name="orientador_update",
    ),
    path(
        "orientadores/<int:pk>/eliminar/",
        OrientadorDeleteView.as_view(),
        name="orientador_delete",
    ),

   

]
