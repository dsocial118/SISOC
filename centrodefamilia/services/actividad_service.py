import logging
from centrodefamilia.models import Actividad

logger = logger = logging.getLogger(__name__)


def actividades_disponibles_para_centro():
    """
    Devuelve todas las actividades cargadas por el técnico
    (puede extenderse para aplicar filtros por centro en el futuro).
    """
    try:
        return Actividad.objects.all()
    except Exception as e:
        logger.error(
            f"Error en Actividad.actividades_disponibles_para_centro para comedor: {e}",
            exc_info=True,
        )
        raise
