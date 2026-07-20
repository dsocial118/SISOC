from .comedor import (
    ComedorCreateView,
    ComedorDatosConvenioPnudUpdateView,
    ComedorDeleteView,
    ComedorDetailView,
    ComedorListView,
    ComedorTransaccionesDetailView,
    ComedorUpdateView,
    descargar_certificacion_prestaciones_web,
)
from .colaborador import (
    ColaboradorEspacioCreateView,
    ColaboradorEspacioDeleteView,
    ColaboradorEspacioUpdateView,
)
from .dupla import AsignarDuplaListView
from .nomina import (
    NominaAsistenciaHistorialView,
    NominaCreateView,
    NominaDeleteView,
    NominaDetailView,
    NominaDirectaCreateView,
    NominaDirectaDeleteView,
    NominaDirectaDetailView,
    NominaImportarView,
    nomina_cambiar_estado,
    nomina_derivar,
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
from .actividades_pnud import (
    ActividadPnudCreateView,
    ActividadPnudDeactivateView,
    ActividadPnudListView,
    ActividadPnudUpdateView,
)
from .actividad_espacio_pwa import (
    ActividadEspacioPWACreateView,
    ActividadEspacioPWAUpdateView,
)

__all__ = [
    "ActividadEspacioPWACreateView",
    "ActividadEspacioPWAUpdateView",
    "ActividadPnudCreateView",
    "ActividadPnudDeactivateView",
    "ActividadPnudListView",
    "ActividadPnudUpdateView",
    "AsignarDuplaListView",
    "ColaboradorEspacioCreateView",
    "ColaboradorEspacioDeleteView",
    "ColaboradorEspacioUpdateView",
    "ComedorCreateView",
    "ComedorDatosConvenioPnudUpdateView",
    "ComedorDeleteView",
    "ComedorDetailView",
    "ComedorListView",
    "ComedorTransaccionesDetailView",
    "ComedorUpdateView",
    "descargar_certificacion_prestaciones_web",
    "NominaCreateView",
    "NominaAsistenciaHistorialView",
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
    "nomina_derivar",
    "nomina_editar_ajax",
    "relevamiento_crear_editar_ajax",
    "capacitacion_certificado_estado_ajax",
    "CursoAppMobileCreateView",
    "CursoAppMobileDeleteView",
    "CursoAppMobileListView",
    "CursoAppMobileUpdateView",
    "validar_comedor",
]
