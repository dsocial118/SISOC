import logging
from datetime import datetime
from pathlib import Path

from django.utils import timezone


class DailyFileHandler(logging.FileHandler):
    def __init__(self, filename, mode="a", encoding=None, delay=False):
        current_date = datetime.now().strftime("%Y-%m-%d")
        daily_folder = Path(filename).parent / current_date
        daily_folder.mkdir(parents=True, exist_ok=True)
        daily_filename = daily_folder / Path(filename).name
        super().__init__(daily_filename, mode, encoding, delay)


def convert_string_to_int(value):
    return int(value) if value != "" else None


def format_fecha_gestionar(fecha_visita: datetime):
    return fecha_visita.strftime("%d/%m/%Y %H:%M")


def format_fecha_django(fecha_visita: str):
    fecha_formateada = datetime.strptime(fecha_visita, "%d/%m/%Y %H:%M")
    return timezone.make_aware(fecha_formateada, timezone.get_default_timezone())


def format_serializer_errors(serializer):
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
