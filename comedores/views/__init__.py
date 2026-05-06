from .comedor import (
    ComedorCreateView,
    ComedorDatosConvenioPnudUpdateView,
    ComedorDeleteView,
    ComedorDetailView,
    ComedorListView,
    ComedorUpdateView,
)
from .colaborador import (
    ColaboradorEspacioCreateView,
    ColaboradorEspacioDeleteView,
    ColaboradorEspacioUpdateView,
)
from .dupla import AsignarDuplaListView
from .nomina import (
    NominaCreateView,
    NominaDeleteView,
    NominaDetailView,
    NominaDirectaCreateView,
    NominaDirectaDeleteView,
    NominaDirectaDetailView,
    NominaImportarView,
    nomina_cambiar_estado,
    nomina_editar_ajax,
)
from .observacion import (
    ObservacionCreateView,
    ObservacionDeleteView,
    ObservacionDetailView,
    ObservacionUpdateView,
)
from .relevamientos import relevamiento_crear_editar_ajax
from .validacion import validar_comedor
from .capacitaciones import capacitacion_certificado_estado_ajax
from .cursos_app_mobile import (
    CursoAppMobileCreateView,
    CursoAppMobileDeleteView,
    CursoAppMobileListView,
    CursoAppMobileUpdateView,
)

__all__ = [
    "AsignarDuplaListView",
    "ColaboradorEspacioCreateView",
    "ColaboradorEspacioDeleteView",
    "ColaboradorEspacioUpdateView",
    "ComedorCreateView",
    "ComedorDatosConvenioPnudUpdateView",
    "ComedorDeleteView",
    "ComedorDetailView",
    "ComedorListView",
    "ComedorUpdateView",
    "NominaCreateView",
    "NominaDeleteView",
    "NominaDetailView",
    "NominaDirectaCreateView",
    "NominaDirectaDeleteView",
    "NominaDirectaDetailView",
    "NominaImportarView",
    "ObservacionCreateView",
    "ObservacionDeleteView",
    "ObservacionDetailView",
    "ObservacionUpdateView",
    "nomina_cambiar_estado",
    "nomina_editar_ajax",
    "relevamiento_crear_editar_ajax",
    "capacitacion_certificado_estado_ajax",
    "CursoAppMobileCreateView",
    "CursoAppMobileDeleteView",
    "CursoAppMobileListView",
    "CursoAppMobileUpdateView",
    "validar_comedor",
]
