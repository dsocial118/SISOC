"""
MÓDULO DEPRECADO - Usar core.decorators en su lugar.
Todos los decoradores fueron migrados a core.decorators.
"""

import warnings

from core.decorators import group_required  # noqa

warnings.warn(
    "configuraciones.decorators está deprecado. Usá core.decorators en su lugar",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["group_required"]
