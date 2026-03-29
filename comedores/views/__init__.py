from .comedor import (
    ComedorCreateView,
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

__all__ = [
    "AsignarDuplaListView",
    "ColaboradorEspacioCreateView",
    "ColaboradorEspacioDeleteView",
    "ColaboradorEspacioUpdateView",
    "ComedorCreateView",
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
    "validar_comedor",
]
