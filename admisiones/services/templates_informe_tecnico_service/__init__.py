"""Alias de compatibilidad para el servicio de templates de Informe Técnico."""

import sys as _sys

from . import impl as _impl

_sys.modules[__name__] = _impl
