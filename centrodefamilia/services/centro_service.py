from centrodefamilia.models import Centro
import logging

logger = logging.getLogger(__name__)

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
        logger.error("Ocurrió un error inesperado en puede_operar", exc_info=True)
        return False

def obtener_centros_adheridos_de_faro(faro):
    """
    Retorna todos los centros adheridos activos vinculados a un faro dado.
    """
    try:
        return Centro.objects.filter(faro_asociado=faro, activo=True)
    except Exception as e:
        logger.error("Ocurrió un error inesperado en obtener_centros_adheridos_de_faro", exc_info=True)
        return Centro.objects.none()