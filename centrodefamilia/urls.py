from django.urls import path
from centrodefamilia.views.centro import CentroListView, CentroCreateView, CentroUpdateView
from centrodefamilia.views.actividad import ActividadCentroListView, ActividadCentroCreateView
from centrodefamilia.views.participante import ParticipanteActividadListView, ParticipanteActividadCreateView
from django.contrib.auth.decorators import login_required
from centrodefamilia.utils.decorators import group_required



urlpatterns = [
    # CENTROS (Técnico)
    path(
        'centros/',
        group_required('tecnico')(CentroListView.as_view()),
        name='centros_listar'
    ),
    path(
        'centros/crear/',
        group_required('tecnico')(CentroCreateView.as_view()),
        name='centros_crear'
    ),
    path(
        'centros/<int:pk>/editar/',
        group_required('tecnico')(CentroUpdateView.as_view()),
        name='centros_editar'
    ),

    # ACTIVIDADES POR CENTRO (Administrador Centro)
    path(
        'centros/<int:centro_id>/actividades/',
        group_required('administrador_centro')(ActividadCentroListView.as_view()),
        name='actividadcentro_listar'
    ),
    path(
        'centros/<int:centro_id>/actividades/crear/',
        group_required('administrador_centro')(ActividadCentroCreateView.as_view()),
        name='actividadcentro_crear'
    ),

    # PARTICIPANTES POR ACTIVIDAD (Administrador Centro)
    path(
        'actividades/<int:actividadcentro_id>/participantes/',
        group_required('administrador_centro')(ParticipanteActividadListView.as_view()),
        name='participante_listar'
    ),
    path(
        'actividades/<int:actividadcentro_id>/participantes/crear/',
        group_required('administrador_centro')(ParticipanteActividadCreateView.as_view()),
        name='participante_crear'
    ),
]