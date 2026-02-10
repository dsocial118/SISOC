"""Utilidades generales usadas en diferentes módulos del proyecto."""

import logging
import json
from datetime import datetime
from pathlib import Path

from django.utils import timezone


class DailyFileHandler(logging.FileHandler):
    """Administrador de archivos que crea un log diario en un subdirectorio.

    Cada instancia genera un archivo de log dentro de una carpeta con la fecha
    actual, facilitando la organización y revisión de registros.
    """

    def __init__(self, filename, mode="a", encoding=None, delay=False):
        """Inicializar el manejador creando una carpeta por día.

        Args:
            filename: Ruta base del archivo de log.
            mode: Modo de apertura del archivo.
            encoding: Codificación utilizada para el archivo.
            delay: Retrasar la creación del archivo hasta el primer registro.
        """

        current_date = timezone.localtime().strftime("%Y-%m-%d")
        daily_folder = Path(filename).parent / current_date
        daily_folder.mkdir(parents=True, exist_ok=True)
        daily_filename = daily_folder / Path(filename).name
        super().__init__(daily_filename, mode, encoding, delay)


class JSONDataFormatter(logging.Formatter):
    """
    Serializa record.data a JSON (una línea por registro).
    Estructura: {"ts": "...", "name": "...", "level": "...", "data": {...}}
    """

    def __init__(self, fmt=None, datefmt=None, style="%", **kwargs):
        super().__init__(fmt=fmt, datefmt=datefmt, style=style)

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, self.datefmt),
            "name": record.name,
            "level": record.levelname,
            "data": getattr(record, "data", None),
        }
        return json.dumps(payload, ensure_ascii=False, default=str)


def convert_string_to_int(value):
    """Convertir una cadena a entero si contiene un valor numérico.

    Args:
        value: Cadena a convertir. Si es cadena vacía retorna ``None``.

    Returns:
        Entero convertido o ``None`` cuando no hay valor.
    """
    try:
        return int(value) if value != "" else None
    except (ValueError, TypeError):
        return None


def format_fecha_gestionar(fecha_visita):
    """Formatear un objeto ``datetime`` a la representación usada por GestionAR."""

    return fecha_visita.strftime("%d/%m/%Y %H:%M")


def format_fecha_django(fecha_visita):
    """Convertir una fecha en formato ``dd/mm/YYYY HH:MM`` a ``datetime``.

    La fecha resultante se marca como consciente de zona horaria utilizando la
    configuración por defecto de Django.

    Args:
        fecha_visita: Cadena con fecha y hora.

    Returns:
        Objeto ``datetime`` con información de zona horaria.
    """

    fecha_formateada = datetime.strptime(fecha_visita, "%d/%m/%Y %H:%M")
    return timezone.make_aware(fecha_formateada, timezone.get_default_timezone())


def format_serializer_errors(serializer):
    """Unir los errores de un serializer en un mensaje legible."""

    error_messages = []
    for field, errors in serializer.errors.items():
        for error in errors:
            if field == "non_field_errors":
                # Errores sin campo específico
                error_messages.append(str(error))
            else:
                error_messages.append(
                    f"{field}: {str(error)}"
                )  # Errores en campos específicos

    error_message_str = " | ".join(error_messages)
    return error_message_str


def format_error_detail(detail):
    """Formatear errores (dict/list/str) en un mensaje legible."""

    error_messages = []

    def _flatten(current_detail, field_path):
        if isinstance(current_detail, dict):
            for key, value in current_detail.items():
                _flatten(value, field_path + [str(key)])
            return

        if isinstance(current_detail, (list, tuple)):
            for item in current_detail:
                _flatten(item, field_path)
            return

        if field_path and field_path[-1] == "non_field_errors":
            error_messages.append(str(current_detail))
            return

        if field_path:
            error_messages.append(f"{'.'.join(field_path)}: {str(current_detail)}")
        else:
            error_messages.append(str(current_detail))

    _flatten(detail, [])
    return " | ".join(error_messages)
