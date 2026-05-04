"""Compatibility alias that preserves original module patch semantics."""

import sys as _sys

from . import impl as _impl
from .impl import registrar_cambio_estado

_sys.modules[__name__] = _impl
