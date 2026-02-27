"""Compatibility alias that preserves original module patch semantics."""

import sys as _sys

from . import impl as _impl

_sys.modules[__name__] = _impl
