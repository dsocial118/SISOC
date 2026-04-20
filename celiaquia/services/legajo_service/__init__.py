"""Compatibility alias that preserves original module patch semantics."""

import sys as _sys

from .impl import LegajoService
from . import impl as _impl

__all__ = ["LegajoService"]

_sys.modules[__name__] = _impl
