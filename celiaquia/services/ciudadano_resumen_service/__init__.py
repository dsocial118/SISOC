"""Read projection used by the public Celiaquía API."""

from .impl import (
    LegajoResumenCiudadano,
    ResumenCiudadano,
    obtener_resumen_ciudadano,
)

__all__ = [
    "LegajoResumenCiudadano",
    "ResumenCiudadano",
    "obtener_resumen_ciudadano",
]
