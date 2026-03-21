from django.urls import path
from core.decorators import permissions_any_required

from VAT.views.centro import (
    CentroCreateView,
    CentroDeleteView,
    CentroDetailView,
    CentroListView,
    CentroUpdateView,
    centros_ajax,
)

from VAT.views.actividad import (
    ActividadCentroCreateView,
    ActividadCentroDetailView,
    ActividadCentroListView,
    ActividadCentroUpdateView,
    ActividadCreateView,
    cargar_actividades_por_categoria,
)

from VAT.views.participante import (
    ParticipanteActividadCreateView,
    ParticipanteActividadDeleteView,
    ParticipanteActividadListEsperaView,
    ParticipanteActividadPromoverView,
)

from .views.encuentro import RegistrarAsistenciaView

from VAT.views.modalidad_institucional import (
    ModalidadInstitucionalListView,
    ModalidadInstitucionalCreateView,
    ModalidadInstitucionalDetailView,
    ModalidadInstitucionalUpdateView,
    ModalidadInstitucionalDeleteView,
)


urlpatterns = [
    path(
        "vat/centros/",
        permissions_any_required(["VAT.view_centro"])(CentroListView.as_view()),
        name="vat_centro_list",
    ),
    path(
        "vat/centros/ajax/",
        permissions_any_required(["VAT.view_centro"])(centros_ajax),
        name="vat_centros_ajax",
    ),
    path(
        "vat/centros/nuevo/",
        permissions_any_required(["VAT.view_centro"])(CentroCreateView.as_view()),
        name="vat_centro_create",
    ),
    path(
        "vat/centros/<int:pk>/editar/",
        permissions_any_required(["VAT.view_centro"])(CentroUpdateView.as_view()),
        name="vat_centro_update",
    ),
    path(
        "vat/centros/<int:pk>/",
        permissions_any_required(["VAT.view_centro"])(CentroDetailView.as_view()),
        name="vat_centro_detail",
    ),
    path(
        "vat/centros/<int:pk>/eliminar/",
        permissions_any_required(["VAT.view_centro"])(CentroDeleteView.as_view()),
        name="vat_centro_delete",
    ),
    path(
        "vat/actividades/",
        permissions_any_required(["VAT.view_centro"])(
            ActividadCentroListView.as_view()
        ),
        name="vat_actividadcentro_list",
    ),
    path(
        "vat/centros/<int:centro_id>/actividades/nueva/",
        permissions_any_required(["VAT.view_centro"])(
            ActividadCentroCreateView.as_view()
        ),
        name="vat_actividadcentro_create",
    ),
    path(
        "vat/centros/actividades/<int:pk>/detalle/",
        permissions_any_required(["VAT.view_centro"])(
            ActividadCentroDetailView.as_view()
        ),
        name="vat_actividadcentro_detail",
    ),
    path(
        "vat/centros/<int:centro_id>/actividades/<int:actividad_id>/participantes/crear/",
        permissions_any_required(["VAT.view_centro"])(
            ParticipanteActividadCreateView.as_view()
        ),
        name="vat_participanteactividad_create",
    ),
    path(
        "vat/centros/actividades/<int:pk>/editar/",
        permissions_any_required(["VAT.view_centro"])(
            ActividadCentroUpdateView.as_view()
        ),
        name="vat_actividadcentro_edit",
    ),
    path(
        "vat/ajax/actividades/",
        permissions_any_required(["VAT.view_centro"])(cargar_actividades_por_categoria),
        name="vat_ajax_cargar_actividades",
    ),
    path(
        "vat/centros/<int:centro_id>/actividades/<int:actividad_id>/participantes/<int:pk>/eliminar/",
        permissions_any_required(["VAT.view_centro"])(
            ParticipanteActividadDeleteView.as_view()
        ),
        name="vat_participanteactividad_delete",
    ),
    path(
        "vat/centros/<int:centro_id>/actividades/<int:actividad_id>/lista-espera/",
        permissions_any_required(["VAT.view_centro"])(
            ParticipanteActividadListEsperaView.as_view()
        ),
        name="vat_actividadcentro_lista_espera",
    ),
    path(
        "vat/centros/<int:centro_id>/actividades/<int:actividad_id>/lista-espera/<int:pk>/promover/",
        permissions_any_required(["VAT.view_centro"])(
            ParticipanteActividadPromoverView.as_view()
        ),
        name="vat_participanteactividad_promover",
    ),
    # Encuentros / Asistencia
    path(
        "vat/encuentros/<int:pk>/asistencia/",
        permissions_any_required(["VAT.view_centro"])(
            RegistrarAsistenciaView.as_view()
        ),
        name="vat_encuentro_asistencia",
    ),
    path(
        "vat/actividades/nueva/",
        permissions_any_required(["VAT.view_centro"])(ActividadCreateView.as_view()),
        name="vat_actividad_create_sola",
    ),
    # Modalidades Institucionales
    path(
        "vat/modalidades-institucionales/",
        permissions_any_required(["VAT.view_modalidadinstitucional"])(
            ModalidadInstitucionalListView.as_view()
        ),
        name="vat_modalidad_institucional_list",
    ),
    path(
        "vat/modalidades-institucionales/nueva/",
        permissions_any_required(["VAT.add_modalidadinstitucional"])(
            ModalidadInstitucionalCreateView.as_view()
        ),
        name="vat_modalidad_institucional_create",
    ),
    path(
        "vat/modalidades-institucionales/<int:pk>/",
        permissions_any_required(["VAT.view_modalidadinstitucional"])(
            ModalidadInstitucionalDetailView.as_view()
        ),
        name="vat_modalidad_institucional_detail",
    ),
    path(
        "vat/modalidades-institucionales/<int:pk>/editar/",
        permissions_any_required(["VAT.change_modalidadinstitucional"])(
            ModalidadInstitucionalUpdateView.as_view()
        ),
        name="vat_modalidad_institucional_update",
    ),
    path(
        "vat/modalidades-institucionales/<int:pk>/eliminar/",
        permissions_any_required(["VAT.delete_modalidadinstitucional"])(
            ModalidadInstitucionalDeleteView.as_view()
        ),
        name="vat_modalidad_institucional_delete",
    ),

]
