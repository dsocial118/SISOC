# DEPRECATED: All utilities migrated to core.utils
# This file is kept for Django compatibility only

import warnings

from core.utils import (  # noqa
    DailyFileHandler,
    convert_string_to_int,
    format_fecha_gestionar,
    format_fecha_django,
    format_serializer_errors,
)

warnings.warn(
    "config.utils is deprecated. Use core.utils instead",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    'DailyFileHandler',
    'convert_string_to_int', 
    'format_fecha_gestionar',
    'format_fecha_django',
    'format_serializer_errors',
]
