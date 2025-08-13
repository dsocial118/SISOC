import logging
from centrodefamilia.models import Centro

logger = logging.getLogger("django")


def puede_operar(centro):
    """
    Verifica si un centro puede operar:
    - Si es tipo 'adherido', debe tener un centro faro activo.
    - Si es tipo 'faro', puede operar directamente.
    """
    try:
        if centro.tipo == "adherido":
            return centro.faro_asociado and centro.faro_asociado.activo
        return True
    except Exception as e:
        logger.error(
            f"Error en AcompanamientoService.puede_operar para centro: {centro} {e}",
            exc_info=True,
        )
        raise


def obtener_centros_adheridos_de_faro(faro):
    """
    Retorna todos los centros adheridos activos vinculados a un faro dado.
    """
    try:
        return Centro.objects.filter(faro_asociado=faro, activo=True)
    except Exception as e:
        logger.error(
            f"Error en AcompanamientoService.obtener_centros_adheridos_de_faro para comedor: {faro} {e}",
            exc_info=True,
        )
        raise
