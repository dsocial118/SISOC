from django.urls import path
from centrodefamilia.views.centro import (
    CentroDeleteView, CentroListView, CentroCreateView, CentroUpdateView, CentroDetailView
)
from centrodefamilia.views.actividad import (
    ActividadCentroListView, ActividadCentroCreateView
)
from centrodefamilia.views.participante import (
    ParticipanteActividadListView, ParticipanteActividadCreateView
)
from centrodefamilia.utils.decorators import group_required

urlpatterns = [
    # --- CENTROS ---
    path('centros/', group_required('superadmin', 'ReferenteCentro')(CentroListView.as_view()), name='centro_list'),
    path('centros/nuevo/', group_required('superadmin', 'ReferenteCentro')(CentroCreateView.as_view()), name='centro_create'),
    path('centros/<int:pk>/editar/', group_required('superadmin', 'ReferenteCentro')(CentroUpdateView.as_view()), name='centro_update'),
    path('centros/<int:pk>/', group_required('superadmin', 'ReferenteCentro')(CentroDetailView.as_view()), name='centro_detail'),
    path('centros/<int:pk>/eliminar/', group_required('superadmin', 'ReferenteCentro')(CentroDeleteView.as_view()), name='centro_delete'),

    # --- ACTIVIDADES ---
    path(
        'actividades/',
        group_required('superadmin', 'ReferenteCentro')(ActividadCentroListView.as_view()),
        name='actividadcentro_list'
    ),
    path(
        'actividades/nueva/',
        group_required('superadmin', 'ReferenteCentro')(ActividadCentroCreateView.as_view()),
        name='actividadcentro_create'
    ),
    path(
        'centros/<int:centro_id>/actividades/nueva/',
        group_required('superadmin', 'ReferenteCentro')(ActividadCentroCreateView.as_view()),
        name='actividadcentro_create'
    ),

    # --- PARTICIPANTES ---
    path(
        'actividades/<int:actividad_id>/participantes/',
        group_required('superadmin', 'ReferenteCentro')(ParticipanteActividadListView.as_view()),
        name='participanteactividad_list'
    ),
    path(
        'actividades/<int:actividad_id>/participantes/nuevo/',
        group_required('superadmin', 'ReferenteCentro')(ParticipanteActividadCreateView.as_view()),
        name='participanteactividad_create'
    ),
]
