import re
from datetime import datetime
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


def procesar_informe(ruta_archivo: str) -> dict:
    """
    Procesa el PDF enviado por CABAL, extrayendo la fecha de periodo y
    devolviendo un dict con los campos necesarios para crear un ExpedienteCabal.

    Se espera que el nombre del archivo tenga formato:
        CABAL_YYYYMMDD_descripcion.pdf

    :param ruta_archivo: Ruta completa al fichero PDF
    :return: dict {
        'fecha_periodo': date,
        'nombre_original': str,
        'ruta': str
    }
    :raises ValidationError: si el nombre no coincide o la fecha es inválida
    """
    try:
        # Extraer solo el nombre del fichero
        nombre = ruta_archivo.split("/")[-1]

        # Buscar la fecha en formato YYYYMMDD
        patron = r"^CABAL_(\d{8})_.*\.pdf$"
        m = re.match(patron, nombre, re.IGNORECASE)
        if not m:
            raise ValidationError(
                f"Nombre de archivo no cumple el patrón esperado: {nombre}"
            )

        fecha_str = m.group(1)
        try:
            fecha = datetime.strptime(fecha_str, "%Y%m%d").date()
        except ValueError as exc:
            raise ValidationError(
                f"Fecha inválida en el nombre de archivo: {fecha_str}"
            ) from exc

        return {
            "fecha_periodo": fecha,
            "nombre_original": nombre,
            "ruta": ruta_archivo,
        }
    except Exception as e:
        logger.error("Ocurrió un error inesperado en procesar_informe", exc_info=True)
        raise
