from .comedor import (
    ComedorCreateView,
    ComedorDeleteView,
    ComedorDetailView,
    ComedorListView,
    ComedorUpdateView,
)
from .dupla import AsignarDuplaListView
from .nomina import (
    NominaCreateView,
    NominaDeleteView,
    NominaDetailView,
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
    "ComedorCreateView",
    "ComedorDeleteView",
    "ComedorDetailView",
    "ComedorListView",
    "ComedorUpdateView",
    "NominaCreateView",
    "NominaDeleteView",
    "NominaDetailView",
    "ObservacionCreateView",
    "ObservacionDeleteView",
    "ObservacionDetailView",
    "ObservacionUpdateView",
    "nomina_editar_ajax",
    "relevamiento_crear_editar_ajax",
    "validar_comedor",
]
