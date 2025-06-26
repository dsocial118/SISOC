"""
DEPRECATED MODULE - Use core.decorators instead
All decorators migrated to core.decorators
"""

import warnings
from core.decorators import *  # noqa

warnings.warn(
    "configuraciones.decorators is deprecated. Use core.decorators instead",
    DeprecationWarning,
    stacklevel=2,
)
