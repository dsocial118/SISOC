"""Servicio para gestión de cruces."""

from .impl import (
    DOCUMENTO_COL_CANDIDATAS,
    CupoNoConfigurado,
    CruceService,
    _WEASY_OK,
)

__all__ = [
    "CruceService",
    "CupoNoConfigurado",
    "DOCUMENTO_COL_CANDIDATAS",
    "_WEASY_OK",
]
