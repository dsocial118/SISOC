"""Compatibility alias that preserves original module patch semantics."""

import sys as _sys

from . import impl as _impl
from .impl import APIClient, RenaperServiceError, consultar_datos_renaper

__all__ = ["APIClient", "RenaperServiceError", "consultar_datos_renaper"]

_sys.modules[__name__] = _impl
