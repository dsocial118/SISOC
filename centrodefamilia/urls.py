# centrodefamilia/urls.py
from django.urls import path
from core.decorators import permissions_any_required

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
    centros_ajax,
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

from .views.beneficiarios import (
    BeneficiariosListView,
    BeneficiariosDetailView,
    ResponsableListView,
    ResponsableDetailView,
    BeneficiariosCreateView,
    BuscarCUILView,
    BuscarResponsableView,
)

urlpatterns = [
    path(
        "centros/<int:centro_id>/informecabal/<int:pk>/",
        permissions_any_required(["CDF SSE"])(InformeCabalArchivoPorCentroDetailView.as_view()),
        name="informecabal_archivo_centro_detail",
    ),
    path(
        "centros/",
        permissions_any_required(["ReferenteCentro", "CDF SSE"])(CentroListView.as_view()),
        name="centro_list",
    ),
    path(
        "centros/ajax/",
        permissions_any_required(["ReferenteCentro", "CDF SSE"])(centros_ajax),
        name="centros_ajax",
    ),
    path(
        "centros/nuevo/",
        permissions_any_required(["ReferenteCentro", "CDF SSE"])(CentroCreateView.as_view()),
        name="centro_create",
    ),
    path(
        "centros/<int:pk>/editar/",
        permissions_any_required(["ReferenteCentro", "CDF SSE"])(CentroUpdateView.as_view()),
        name="centro_update",
    ),
    path(
        "centros/<int:pk>/",
        permissions_any_required(["ReferenteCentro", "CDF SSE"])(CentroDetailView.as_view()),
        name="centro_detail",
    ),
    path(
        "centros/<int:pk>/eliminar/",
        permissions_any_required(["ReferenteCentro", "CDF SSE"])(CentroDeleteView.as_view()),
        name="centro_delete",
    ),
    path(
        "actividades/",
        permissions_any_required(["ReferenteCentro", "CDF SSE"])(
            ActividadCentroListView.as_view()
        ),
        name="actividadcentro_list",
    ),
    path(
        "centros/<int:centro_id>/actividades/nueva/",
        permissions_any_required(["ReferenteCentro", "CDF SSE"])(
            ActividadCentroCreateView.as_view()
        ),
        name="actividadcentro_create",
    ),
    path(
        "centros/actividades/<int:pk>/detalle/",
        permissions_any_required(["ReferenteCentro", "CDF SSE"])(
            ActividadCentroDetailView.as_view()
        ),
        name="actividadcentro_detail",
    ),
    path(
        "centros/<int:centro_id>/actividades/<int:actividad_id>/participantes/crear/",
        permissions_any_required(["ReferenteCentro", "CDF SSE"])(
            ParticipanteActividadCreateView.as_view()
        ),
        name="participanteactividad_create",
    ),
    path(
        "centros/actividades/<int:pk>/editar/",
        permissions_any_required(["ReferenteCentro", "CDF SSE"])(
            ActividadCentroUpdateView.as_view()
        ),
        name="actividadcentro_edit",
    ),
    path(
        "ajax/actividades/",
        permissions_any_required(["ReferenteCentro", "CDF SSE"])(
            cargar_actividades_por_categoria
        ),
        name="ajax_cargar_actividades",
    ),
    path(
        "centros/<int:centro_id>/actividades/<int:actividad_id>/participantes/<int:pk>/eliminar/",
        permissions_any_required(["ReferenteCentro", "CDF SSE"])(
            ParticipanteActividadDeleteView.as_view()
        ),
        name="participanteactividad_delete",
    ),
    path(
        "centros/<int:centro_id>/actividades/<int:actividad_id>/lista-espera/",
        permissions_any_required(["ReferenteCentro", "CDF SSE"])(
            ParticipanteActividadListEsperaView.as_view()
        ),
        name="actividadcentro_lista_espera",
    ),
    path(
        "centros/<int:centro_id>/actividades/<int:actividad_id>/lista-espera/<int:pk>/promover/",
        permissions_any_required(["ReferenteCentro", "CDF SSE"])(
            ParticipanteActividadPromoverView.as_view()
        ),
        name="participanteactividad_promover",
    ),
    # ——— NUEVO: Informe CABAL ———
    path(
        "informecabal/",
        permissions_any_required(["CDF SSE"])(InformeCabalListView.as_view()),
        name="informecabal_list",
    ),
    path(
        "informecabal/preview/",
        permissions_any_required(["CDF SSE"])(InformeCabalPreviewAjaxView.as_view()),
        name="informecabal_preview",
    ),
    path(
        "informecabal/<int:pk>/",
        permissions_any_required(["CDF SSE"])(InformeCabalArchivoDetailView.as_view()),
        name="informecabal_archivo_detail",
    ),
    path(
        "informecabal/process/",
        permissions_any_required(["CDF SSE"])(InformeCabalProcessAjaxView.as_view()),
        name="informecabal_process",
    ),
    path(
        "informecabal/registro/<int:pk>/",
        permissions_any_required(["CDF SSE"])(InformeCabalRegistroDetailView.as_view()),
        name="informecabal_registro_detail",
    ),
    # (Dejamos tus rutas previas de “expedientes” intactas, aunque NO se usan en este flujo)
    path(
        "actividades/nueva/",
        permissions_any_required(["CDF SSE"])(ActividadCreateView.as_view()),
        name="actividad_create_sola",
    ),
    # repro
    path(
        "informecabal/reprocess/",
        permissions_any_required(["CDF SSE"])(InformeCabalReprocessCenterAjaxView.as_view()),
        name="informecabal_reprocess_center",
    ),
    # URLs de Beneficiarios
    path(
        "beneficiarios/beneficiarios/",
        permissions_any_required(["CDF SSE"])(BeneficiariosListView.as_view()),
        name="beneficiarios_list",
    ),
    path(
        "beneficiarios/beneficiarios/<int:pk>/",
        permissions_any_required(["CDF SSE"])(BeneficiariosDetailView.as_view()),
        name="beneficiarios_detail",
    ),
    path(
        "beneficiarios/nuevo/",
        permissions_any_required(["CDF SSE"])(BeneficiariosCreateView.as_view()),
        name="beneficiarios_crear",
    ),
    path(
        "beneficiarios/responsables/",
        permissions_any_required(["CDF SSE"])(ResponsableListView.as_view()),
        name="responsables_list",
    ),
    path(
        "beneficiarios/responsables/<int:pk>/",
        permissions_any_required(["CDF SSE"])(ResponsableDetailView.as_view()),
        name="responsables_detail",
    ),
    path(
        "beneficiarios/buscar-cuil/",
        permissions_any_required(["CDF SSE"])(BuscarCUILView.as_view()),
        name="buscar_cuil",
    ),
    path(
        "beneficiarios/buscar-responsable/",
        permissions_any_required(["CDF SSE"])(BuscarResponsableView.as_view()),
        name="buscar_responsable",
    ),
]
