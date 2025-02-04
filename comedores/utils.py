import datetime
from django.utils import timezone


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


def format_fecha_django(fecha_visita: str):
    fecha_formateada = datetime.datetime.strptime(fecha_visita, "%d/%m/%Y %H:%M")
    return timezone.make_aware(fecha_formateada, timezone.get_default_timezone())


def format_fecha_gestionar(fecha_visita: datetime.datetime):
    return fecha_visita.strftime("%d/%m/%Y %H:%M")
