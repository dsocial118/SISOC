from centrodefamilia.models import Actividad
import logging

logger = logging.getLogger(__name__)


def actividades_disponibles_para_centro():
    """
    Devuelve todas las actividades cargadas por el técnico
    (puede extenderse para aplicar filtros por centro en el futuro).
    """
    try:
        return Actividad.objects.all()
    except Exception as e:
        logger.error(
            "Ocurrió un error inesperado en actividades_disponibles_para_centro",
            exc_info=True,
        )
        return Actividad.objects.none()
