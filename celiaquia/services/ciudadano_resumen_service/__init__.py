"""Compatibility alias for the citizen-summary service implementation."""

import sys as _sys

from . import impl as _impl

_sys.modules[__name__] = _impl
